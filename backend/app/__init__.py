"""
BackupGenie - Automated Multi-Source Backup Manager
Main Application Module
"""
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_babel import Babel
from app.config import Config

db = SQLAlchemy()
babel = Babel()


def get_locale():
    """Get locale from request header or default to English"""
    return request.headers.get('Accept-Language', 'en').split(',')[0][:2]


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Babel configuration
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'de']
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

    # Initialize extensions
    db.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from app.api.backup import backup_bp
    from app.api.sources import sources_bp
    from app.api.auth import auth_bp
    from app.api.notifications import notifications_bp

    app.register_blueprint(backup_bp, url_prefix='/api/v1/backup')
    app.register_blueprint(sources_bp, url_prefix='/api/v1/sources')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(notifications_bp, url_prefix='/api/v1/notifications')

    # Create database tables
    with app.app_context():
        db.create_all()

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'version': '1.0.0'}

    return app
