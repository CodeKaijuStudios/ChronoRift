"""
ChronoRift Flask Application Factory
Creates and configures the Flask application with all extensions
"""

import logging
import logging.handlers
import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_caching import Cache
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.config import get_config


# Initialize extensions
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO()
cache = Cache()


def create_app(config_name: str = None) -> Flask:
    """
    Application factory function
    
    Args:
        config_name: Configuration environment (development, testing, production)
        
    Returns:
        Configured Flask application instance
    """
    # Get configuration
    config = get_config(config_name)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize extensions
    _init_extensions(app)
    
    # Configure logging
    _configure_logging(app)
    
    # Configure error handlers
    _configure_error_handlers(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Configure WebSocket events
    _configure_websocket(app)
    
    # Configure monitoring (Sentry)
    if app.config.get('SENTRY_DSN'):
        _configure_sentry(app)
    
    # Add shell context
    app.shell_context_processor(shell_context)
    
    return app


def _init_extensions(app: Flask) -> None:
    """Initialize Flask extensions"""
    
    # Database ORM
    from app.models import db
    db.init_app(app)
    migrate.init_app(app, db)
    
    # JWT Authentication
    jwt.init_app(app)
    
    # CORS
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}},
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
        supports_credentials=app.config['CORS_ALLOW_CREDENTIALS'],
        max_age=app.config['CORS_MAX_AGE']
    )
    
    # Rate Limiting
    if app.config['RATE_LIMITING_ENABLED']:
        limiter.init_app(app)
    
    # WebSocket
    socketio.init_app(
        app,
        cors_allowed_origins=app.config['CORS_ORIGINS'],
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        ping_timeout=app.config['SOCKETIO_PING_TIMEOUT'],
        ping_interval=app.config['SOCKETIO_PING_INTERVAL'],
        message_queue=app.config['SOCKETIO_MESSAGE_QUEUE']
    )
    
    # Caching
    cache.init_app(app)


def _configure_logging(app: Flask) -> None:
    """Configure application logging"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Get logger
    logger = logging.getLogger('chronorift')
    logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(app.config['LOG_FORMAT'])
    
    # File handler
    if app.config['LOG_TO_FILE']:
        file_handler = logging.handlers.RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if app.config['LOG_TO_CONSOLE']:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Set Flask app logger
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)


def _configure_error_handlers(app: Flask) -> None:
    """Configure error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request"""
        return jsonify({
            'status': 'error',
            'code': 400,
            'message': 'Bad Request',
            'details': str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized"""
        return jsonify({
            'status': 'error',
            'code': 401,
            'message': 'Unauthorized',
            'details': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden"""
        return jsonify({
            'status': 'error',
            'code': 403,
            'message': 'Forbidden',
            'details': 'Access denied'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found"""
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': 'Not Found',
            'details': f'Resource not found: {request.path}'
        }), 404
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity"""
        return jsonify({
            'status': 'error',
            'code': 422,
            'message': 'Unprocessable Entity',
            'details': 'Invalid request data'
        }), 422
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Rate Limit Exceeded"""
        return jsonify({
            'status': 'error',
            'code': 429,
            'message': 'Rate Limit Exceeded',
            'details': 'Too many requests. Please try again later.'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error"""
        app.logger.error(f'Internal Server Error: {error}')
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal Server Error',
            'details': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 Service Unavailable"""
        return jsonify({
            'status': 'error',
            'code': 503,
            'message': 'Service Unavailable',
            'details': 'Server is temporarily unavailable'
        }), 503


def _register_blueprints(app: Flask) -> None:
    """Register application blueprints (routes)"""
    
    # Import blueprints
    from app.routes.auth import auth_bp
    from app.routes.riftwalker import riftwalker_bp
    from app.routes.echoes import echoes_bp
    from app.routes.world import world_bp
    from app.routes.combat import combat_bp
    from app.routes.rifts import rifts_bp
    from app.routes.economy import economy_bp
    from app.routes.social import social_bp
    from app.routes.health import health_bp
    
    # Register blueprints with URL prefix
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(riftwalker_bp, url_prefix='/api/riftwalker')
    app.register_blueprint(echoes_bp, url_prefix='/api/echoes')
    app.register_blueprint(world_bp, url_prefix='/api/world')
    app.register_blueprint(combat_bp, url_prefix='/api/combat')
    app.register_blueprint(rifts_bp, url_prefix='/api/rifts')
    app.register_blueprint(economy_bp, url_prefix='/api/economy')
    app.register_blueprint(social_bp, url_prefix='/api/social')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    
    app.logger.info('All blueprints registered successfully')


def _configure_websocket(app: Flask) -> None:
    """Configure WebSocket event handlers"""
    
    from app.events.ws_events import register_websocket_events
    
    with app.app_context():
        register_websocket_events(socketio)
    
    app.logger.info('WebSocket events registered')


def _configure_sentry(app: Flask) -> None:
    """Configure Sentry error tracking"""
    
    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[
            FlaskIntegration(),
            SqlalchemyIntegration()
        ],
        environment=app.config['SENTRY_ENVIRONMENT'],
        traces_sample_rate=app.config['SENTRY_TRACES_SAMPLE_RATE'],
        send_default_pii=False
    )
    
    app.logger.info(f"Sentry initialized for {app.config['SENTRY_ENVIRONMENT']} environment")


def shell_context():
    """Register shell context for Flask shell"""
    from app.models import db
    
    return {
        'db': db,
        'create_app': create_app,
    }


# JWT callback functions
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from JWT token"""
    from app.models import Riftwalker
    
    identity = jwt_data["sub"]
    return Riftwalker.query.get(identity)


@jwt.additional_claims_loader
def add_claims_to_jwt(identity):
    """Add additional claims to JWT token"""
    from app.models import Riftwalker
    
    user = Riftwalker.query.get(identity)
    if user:
        return {
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'faction': user.faction_id
        }
    return {}


# Global request/response hooks
@app.before_request
def before_request():
    """Execute before each request"""
    request.start_time = datetime.utcnow()


@app.after_request
def after_request(response):
    """Execute after each request"""
    if hasattr(request, 'start_time'):
        elapsed = (datetime.utcnow() - request.start_time).total_seconds()
        response.headers['X-Process-Time'] = str(elapsed)
    return response
