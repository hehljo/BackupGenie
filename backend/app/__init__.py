"""
BackupGenie - Automated Multi-Source Backup Manager
Main Application Module
"""
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from sqlalchemy import text
import os
import logging
from logging.handlers import RotatingFileHandler
from app.config import Config

db = SQLAlchemy()
babel = Babel()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


def get_locale():
    """Get locale from request header or default to English"""
    return request.headers.get('Accept-Language', 'en').split(',')[0][:2]


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Validate critical security settings
    config_class.validate()

    # Babel configuration
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'de']
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

    # Initialize extensions
    db.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    limiter.init_app(app)

    # CORS Configuration - Restrict to allowed origins
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept-Language"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    # Security Headers (disabled force_https for development, enable in production behind proxy)
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'"],  # Tailwind requires unsafe-inline
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", "data:", "https:"],
        'font-src': ["'self'", "data:"],
        'connect-src': ["'self'"],
    }
    Talisman(app,
        force_https=False,  # Set to True in production with HTTPS
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src']
    )

    # Register blueprints
    from app.api.backup import backup_bp
    from app.api.sources import sources_bp
    from app.api.auth import auth_bp
    from app.api.notifications import notifications_bp
    from app.api.settings import settings_bp
    from app.api.config import config_bp

    app.register_blueprint(backup_bp, url_prefix='/api/v1/backup')
    app.register_blueprint(sources_bp, url_prefix='/api/v1/sources')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(notifications_bp, url_prefix='/api/v1/notifications')
    app.register_blueprint(settings_bp, url_prefix='/api/v1/settings')
    app.register_blueprint(config_bp, url_prefix='/api/v1/config')

    # Configure file logging
    log_dir = os.path.dirname(Config.LOG_FILE)
    if os.path.isdir(log_dir):
        file_handler = RotatingFileHandler(
            Config.LOG_FILE, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        ))
        app.logger.addHandler(file_handler)
        logging.getLogger().addHandler(file_handler)

    # Create database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Database tables may already exist: {e}")

        # Bootstrap admin user if no users exist
        from app.models.backup import User
        from werkzeug.security import generate_password_hash
        from sqlalchemy.exc import IntegrityError

        try:
            if User.query.count() == 0:
                import secrets
                default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', '')
                if not default_password:
                    # Generate random password meeting strength requirements
                    default_password = secrets.token_urlsafe(12) + 'A1!'
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash(default_password)
                )
                db.session.add(admin)
                db.session.commit()
                # Log password only once, only to container stdout (not to file)
                print(f"[INIT] Admin user created. Password: {default_password}")
                print("[INIT] Change this password immediately via Settings → User!")
                app.logger.info("Bootstrap: Admin user created. Check container stdout for password.")
        except IntegrityError:
            # User already exists (race condition with multiple workers)
            db.session.rollback()
            app.logger.info("Bootstrap: Admin user already exists, skipping creation")

    @app.route('/health')
    @limiter.exempt  # Exclude health check from rate limiting
    def health():
        """Enhanced health check with database connectivity test"""
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            db_status = 'ok'
        except Exception as e:
            db_status = f'error: {str(e)}'
            return jsonify({
                'status': 'unhealthy',
                'version': '1.0.0',
                'database': db_status
            }), 503

        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'database': db_status
        }), 200

    return app
