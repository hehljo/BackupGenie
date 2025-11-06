"""
BackupGenie - Automated Multi-Source Backup Manager
Main Application Module
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from app.api.backup import backup_bp
    from app.api.sources import sources_bp
    from app.api.auth import auth_bp

    app.register_blueprint(backup_bp, url_prefix='/api/v1/backup')
    app.register_blueprint(sources_bp, url_prefix='/api/v1/sources')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    # Create database tables
    with app.app_context():
        db.create_all()

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'version': '1.0.0'}

    return app
