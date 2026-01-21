"""
ChronoRift Configuration Module
Handles all application configuration settings for different environments
"""

import os
from datetime import timedelta
from decouple import config, Csv


class Config:
    """Base configuration - shared across all environments"""

    # Flask Settings
    SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # Application
    FLASK_APP = config('FLASK_APP', default='run.py')
    FLASK_ENV = config('FLASK_ENV', default='development')
    BASE_URL = config('BASE_URL', default='http://localhost:5000')

    # Database Settings
    SQLALCHEMY_DATABASE_URI = config(
        'DATABASE_URL',
        default='postgresql://chronorift_user:chronorift_password@localhost:5432/chronorift_dev'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = config('SQLALCHEMY_ECHO', default=False, cast=bool)

    # Connection Pool Settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': config('DB_POOL_SIZE', default=20, cast=int),
        'pool_recycle': config('DB_POOL_RECYCLE', default=3600, cast=int),
        'pool_pre_ping': True,
        'max_overflow': config('DB_MAX_OVERFLOW', default=40, cast=int),
        'pool_timeout': config('DB_POOL_TIMEOUT', default=30, cast=int),
    }

    # Redis Settings
    REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
    REDIS_CACHE_URL = config('REDIS_CACHE_URL', default='redis://localhost:6379/1')
    REDIS_SESSION_URL = config('REDIS_SESSION_URL', default='redis://localhost:6379/2')
    REDIS_MAX_CONNECTIONS = config('REDIS_MAX_CONNECTIONS', default=50, cast=int)
    REDIS_SOCKET_TIMEOUT = config('REDIS_SOCKET_TIMEOUT', default=5, cast=int)

    # Caching Settings
    CACHE_TYPE = config('CACHE_TYPE', default='redis')
    CACHE_DEFAULT_TIMEOUT = config('CACHE_DEFAULT_TIMEOUT', default=300, cast=int)
    CACHE_KEY_PREFIX = config('CACHE_KEY_PREFIX', default='chronorift:')
    CACHE_REDIS_URL = REDIS_CACHE_URL

    # JWT Settings
    JWT_SECRET_KEY = config('JWT_SECRET_KEY', default='dev-jwt-secret-key-change-in-production')
    JWT_ALGORITHM = config('JWT_ALGORITHM', default='HS256')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=config('JWT_ACCESS_TOKEN_EXPIRES', default=3600, cast=int)
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=config('JWT_REFRESH_TOKEN_EXPIRES', default=2592000, cast=int)
    )
    JWT_EMAIL_VERIFICATION_EXPIRES = timedelta(
        seconds=config('JWT_EMAIL_VERIFICATION_EXPIRES', default=86400, cast=int)
    )
    JWT_ISSUER = config('JWT_ISSUER', default='chronorift-api')
    JWT_AUDIENCE = config('JWT_AUDIENCE', default='chronorift-client')

    # CORS Settings
    CORS_ORIGINS = config(
        'CORS_ORIGINS',
        default='http://localhost:3000,http://localhost:5000,https://chronorift.com',
        cast=Csv()
    )
    CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=True, cast=bool)
    CORS_MAX_AGE = config('CORS_MAX_AGE', default=3600, cast=int)

    # WebSocket Settings
    SOCKETIO_PROTOCOL_VERSION = config('SOCKETIO_PROTOCOL_VERSION', default=4, cast=int)
    SOCKETIO_PING_TIMEOUT = config('SOCKETIO_PING_TIMEOUT', default=60, cast=int)
    SOCKETIO_PING_INTERVAL = config('SOCKETIO_PING_INTERVAL', default=25, cast=int)
    SOCKETIO_MESSAGE_QUEUE = config('SOCKETIO_MESSAGE_QUEUE', default='redis://localhost:6379/3')
    SOCKETIO_ASYNC_MODE = config('SOCKETIO_ASYNC_MODE', default='gevent')
    SOCKETIO_ENGINEIO_LOGGER = config('SOCKETIO_ENGINEIO_LOGGER', default=False, cast=bool)
    SOCKETIO_SOCKETIO_LOGGER = config('SOCKETIO_SOCKETIO_LOGGER', default=False, cast=bool)

    # Celery Settings
    CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/4')
    CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/5')
    CELERY_TASK_SERIALIZER = config('CELERY_TASK_SERIALIZER', default='json')
    CELERY_RESULT_SERIALIZER = config('CELERY_RESULT_SERIALIZER', default='json')
    CELERY_ACCEPT_CONTENT = config('CELERY_ACCEPT_CONTENT', default='json', cast=Csv())
    CELERY_TASK_SOFT_TIME_LIMIT = config('CELERY_TASK_SOFT_TIME_LIMIT', default=3600, cast=int)
    CELERY_TASK_TIME_LIMIT = config('CELERY_TASK_TIME_LIMIT', default=3600, cast=int)
    CELERY_RESULT_EXPIRES = config('CELERY_RESULT_EXPIRES', default=3600, cast=int)

    # APScheduler Settings
    APSCHEDULER_JOBSTORE_URL = config(
        'APSCHEDULER_JOBSTORE_URL',
        default='postgresql://chronorift_user:chronorift_password@localhost:5432/chronorift_dev'
    )
    APSCHEDULER_EXECUTORS_DEFAULT_POOL_SIZE = config(
        'APSCHEDULER_EXECUTORS_DEFAULT_POOL_SIZE',
        default=20,
        cast=int
    )

    # Email Settings
    MAIL_PROVIDER = config('MAIL_PROVIDER', default='smtp')
    MAIL_SERVER = config('MAIL_SERVER', default='smtp.gmail.com')
    MAIL_PORT = config('MAIL_PORT', default=587, cast=int)
    MAIL_USE_TLS = config('MAIL_USE_TLS', default=True, cast=bool)
    MAIL_USERNAME = config('MAIL_USERNAME', default='')
    MAIL_PASSWORD = config('MAIL_PASSWORD', default='')
    MAIL_DEFAULT_SENDER = config('MAIL_DEFAULT_SENDER', default='noreply@chronorift.com')
    MAIL_SUPPORT_EMAIL = config('MAIL_SUPPORT_EMAIL', default='support@chronorift.com')
    MAIL_BUSINESS_EMAIL = config('MAIL_BUSINESS_EMAIL', default='business@chronorift.com')

    # SendGrid Settings
    SENDGRID_API_KEY = config('SENDGRID_API_KEY', default='')

    # AWS Settings
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
    AWS_REGION = config('AWS_REGION', default='us-east-1')
    S3_BUCKET_NAME = config('S3_BUCKET_NAME', default='chronorift-assets')
    S3_BUCKET_REGION = config('S3_BUCKET_REGION', default='us-east-1')
    CDN_URL = config('CDN_URL', default='https://cdn.chronorift.com')
    CLOUDFRONT_DISTRIBUTION_ID = config('CLOUDFRONT_DISTRIBUTION_ID', default='')

    # OAuth Settings
    DISCORD_CLIENT_ID = config('DISCORD_CLIENT_ID', default='')
    DISCORD_CLIENT_SECRET = config('DISCORD_CLIENT_SECRET', default='')
    DISCORD_REDIRECT_URI = config(
        'DISCORD_REDIRECT_URI',
        default='http://localhost:5000/auth/discord/callback'
    )

    GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')
    GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='')
    GOOGLE_REDIRECT_URI = config(
        'GOOGLE_REDIRECT_URI',
        default='http://localhost:5000/auth/google/callback'
    )

    GITHUB_CLIENT_ID = config('GITHUB_CLIENT_ID', default='')
    GITHUB_CLIENT_SECRET = config('GITHUB_CLIENT_SECRET', default='')
    GITHUB_REDIRECT_URI = config(
        'GITHUB_REDIRECT_URI',
        default='http://localhost:5000/auth/github/callback'
    )

    # Monitoring Settings
    SENTRY_DSN = config('SENTRY_DSN', default='')
    SENTRY_ENVIRONMENT = config('SENTRY_ENVIRONMENT', default='development')
    SENTRY_TRACES_SAMPLE_RATE = config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float)

    NEW_RELIC_CONFIG_FILE = config('NEW_RELIC_CONFIG_FILE', default='newrelic.ini')
    NEW_RELIC_ENVIRONMENT = config('NEW_RELIC_ENVIRONMENT', default='development')
    NEW_RELIC_LOG_LEVEL = config('NEW_RELIC_LOG_LEVEL', default='info')

    APPINSIGHTS_INSTRUMENTATION_KEY = config('APPINSIGHTS_INSTRUMENTATION_KEY', default='')

    # Game Settings
    GAME_DIFFICULTY = config('GAME_DIFFICULTY', default='normal')
    GAME_PVP_ENABLED = config('GAME_PVP_ENABLED', default=True, cast=bool)
    GAME_TRADING_ENABLED = config('GAME_TRADING_ENABLED', default=True, cast=bool)
    GAME_SEASONAL_EVENTS = config('GAME_SEASONAL_EVENTS', default=True, cast=bool)

    # Rift Configuration
    RIFT_SPAWN_INTERVAL = config('RIFT_SPAWN_INTERVAL', default=300, cast=int)
    RIFT_MAX_CONCURRENT = config('RIFT_MAX_CONCURRENT', default=50, cast=int)
    RIFT_DESPAWN_TIMEOUT = config('RIFT_DESPAWN_TIMEOUT', default=1800, cast=int)

    # Echo Configuration
    ECHO_MAX_PER_PLAYER = config('ECHO_MAX_PER_PLAYER', default=6, cast=int)
    ECHO_INITIAL_LEVEL = config('ECHO_INITIAL_LEVEL', default=1, cast=int)
    ECHO_MAX_LEVEL = config('ECHO_MAX_LEVEL', default=100, cast=int)

    # Economy Settings
    STARTING_BALANCE = config('STARTING_BALANCE', default=1000, cast=int)
    ECHO_CAPTURE_REWARD = config('ECHO_CAPTURE_REWARD', default=50, cast=int)
    RIFT_STABILIZE_REWARD = config('RIFT_STABILIZE_REWARD', default=100, cast=int)
    FACTION_CONTROL_REWARD = config('FACTION_CONTROL_REWARD', default=500, cast=int)

    # Combat Settings
    COMBAT_TURN_TIME_LIMIT = config('COMBAT_TURN_TIME_LIMIT', default=30, cast=int)
    COMBAT_MAX_PARTY_SIZE = config('COMBAT_MAX_PARTY_SIZE', default=6, cast=int)
    PVP_LEVEL_RESTRICTION = config('PVP_LEVEL_RESTRICTION', default=10, cast=int)

    # Bonding System
    BONDING_BASE_RATE = config('BONDING_BASE_RATE', default=1.0, cast=float)
    BONDING_MAX_LEVEL = config('BONDING_MAX_LEVEL', default=10, cast=int)
    BONDING_UNLOCK_ABILITY_THRESHOLD = config('BONDING_UNLOCK_ABILITY_THRESHOLD', default=5, cast=int)

    # Guild Settings
    GUILD_MAX_MEMBERS = config('GUILD_MAX_MEMBERS', default=100, cast=int)
    GUILD_CREATION_COST = config('GUILD_CREATION_COST', default=5000, cast=int)
    GUILD_TERRITORY_CONTROL_ENABLED = config('GUILD_TERRITORY_CONTROL_ENABLED', default=True, cast=bool)

    # Rate Limiting
    RATE_LIMIT_API = config('RATE_LIMIT_API', default=100, cast=int)
    RATE_LIMIT_AUTH = config('RATE_LIMIT_AUTH', default=10, cast=int)
    RATE_LIMIT_COMBAT = config('RATE_LIMIT_COMBAT', default=30, cast=int)
    RATE_LIMIT_TRADING = config('RATE_LIMIT_TRADING', default=20, cast=int)
    RATE_LIMITING_ENABLED = config('RATE_LIMITING_ENABLED', default=True, cast=bool)

    # Logging Configuration
    LOG_LEVEL = config('LOG_LEVEL', default='INFO')
    LOG_FILE = config('LOG_FILE', default='logs/chronorift.log')
    LOG_MAX_BYTES = config('LOG_MAX_BYTES', default=10485760, cast=int)
    LOG_BACKUP_COUNT = config('LOG_BACKUP_COUNT', default=5, cast=int)
    LOG_FORMAT = config(
        'LOG_FORMAT',
        default='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    LOG_TO_FILE = config('LOG_TO_FILE', default=True, cast=bool)
    LOG_TO_CONSOLE = config('LOG_TO_CONSOLE', default=True, cast=bool)

    # Feature Flags
    FEATURE_ADVANCED_BONDING = config('FEATURE_ADVANCED_BONDING', default=True, cast=bool)
    FEATURE_FACTION_WARFARE = config('FEATURE_FACTION_WARFARE', default=True, cast=bool)
    FEATURE_TRADING_MARKETPLACE = config('FEATURE_TRADING_MARKETPLACE', default=True, cast=bool)
    FEATURE_SEASONAL_EVENTS = config('FEATURE_SEASONAL_EVENTS', default=True, cast=bool)
    FEATURE_PVP_BATTLES = config('FEATURE_PVP_BATTLES', default=True, cast=bool)
    FEATURE_GUILD_RAIDS = config('FEATURE_GUILD_RAIDS', default=True, cast=bool)
    FEATURE_ECHO_BREEDING = config('FEATURE_ECHO_BREEDING', default=False, cast=bool)

    # Security Settings
    ENFORCE_HTTPS = config('ENFORCE_HTTPS', default=False, cast=bool)
    HSTS_ENABLED = config('HSTS_ENABLED', default=False, cast=bool)
    HSTS_MAX_AGE = config('HSTS_MAX_AGE', default=31536000, cast=int)
    CSP_ENABLED = config('CSP_ENABLED', default=False, cast=bool)
    CSP_DEFAULT_SRC = config('CSP_DEFAULT_SRC', default="'self'")
    CSRF_ENABLED = config('CSRF_ENABLED', default=True, cast=bool)

    # Password Requirements
    PASSWORD_MIN_LENGTH = config('PASSWORD_MIN_LENGTH', default=8, cast=int)
    PASSWORD_REQUIRE_UPPERCASE = config('PASSWORD_REQUIRE_UPPERCASE', default=True, cast=bool)
    PASSWORD_REQUIRE_NUMBERS = config('PASSWORD_REQUIRE_NUMBERS', default=True, cast=bool)
    PASSWORD_REQUIRE_SPECIAL_CHARS = config('PASSWORD_REQUIRE_SPECIAL_CHARS', default=True, cast=bool)

    # Admin & Moderation
    ADMIN_PANEL_ENABLED = config('ADMIN_PANEL_ENABLED', default=True, cast=bool)
    ADMIN_PANEL_URL = config('ADMIN_PANEL_URL', default='/admin')
    ADMIN_SECRET_TOKEN = config('ADMIN_SECRET_TOKEN', default='')
    AUTO_MODERATION_ENABLED = config('AUTO_MODERATION_ENABLED', default=True, cast=bool)
    PROFANITY_FILTER_ENABLED = config('PROFANITY_FILTER_ENABLED', default=True, cast=bool)
    SPAM_DETECTION_ENABLED = config('SPAM_DETECTION_ENABLED', default=True, cast=bool)

    # Support Settings
    SUPPORT_EMAIL = config('SUPPORT_EMAIL', default='support@chronorift.com')
    BUSINESS_EMAIL = config('BUSINESS_EMAIL', default='business@chronorift.com')
    DISCORD_SERVER_INVITE = config('DISCORD_SERVER_INVITE', default='https://discord.gg/codekaiju')
    SUPPORT_SYSTEM_ENABLED = config('SUPPORT_SYSTEM_ENABLED', default=True, cast=bool)
    SUPPORT_API_KEY = config('SUPPORT_API_KEY', default='')


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    FLASK_ENV = 'development'
    SQLALCHEMY_ECHO = True
    DEBUG_TOOLBAR_ENABLED = True
    QUERY_PROFILING_ENABLED = True


class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    FLASK_ENV = 'testing'
    
    # Use separate test database
    SQLALCHEMY_DATABASE_URI = config(
        'TEST_DATABASE_URL',
        default='postgresql://chronorift_user:chronorift_password@localhost:5432/chronorift_test'
    )
    
    # Disable rate limiting in tests
    RATE_LIMITING_ENABLED = False
    
    # Disable auth tokens in tests (for easier testing)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=365)
    
    # Use in-memory cache for tests
    CACHE_TYPE = 'simple'
    
    # Disable CSRF for testing
    CSRF_ENABLED = False
    
    # Faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    FLASK_ENV = 'production'
    SQLALCHEMY_ECHO = False
    
    # Security settings for production
    ENFORCE_HTTPS = True
    HSTS_ENABLED = True
    CSP_ENABLED = True
    CSRF_ENABLED = True
    
    # Production database (should use RDS or managed PostgreSQL)
    SQLALCHEMY_DATABASE_URI = config(
        'DATABASE_URL',
        default='postgresql://user:password@db.example.com:5432/chronorift_prod'
    )
    
    # Larger connection pools for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': config('DB_POOL_SIZE', default=50, cast=int),
        'pool_recycle': config('DB_POOL_RECYCLE', default=3600, cast=int),
        'pool_pre_ping': True,
        'max_overflow': config('DB_MAX_OVERFLOW', default=100, cast=int),
        'pool_timeout': config('DB_POOL_TIMEOUT', default=30, cast=int),
    }
    
    # Enable monitoring in production
    SENTRY_DSN = config('SENTRY_DSN', default='')
    NEW_RELIC_ENVIRONMENT = 'production'


# Configuration dictionary for easy access
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """Get configuration object based on environment
    
    Args:
        env: Environment name (development, testing, production)
        
    Returns:
        Configuration object for the specified environment
    """
    if env is None:
        env = config('FLASK_ENV', default='development')
    
    return config_by_name.get(env, DevelopmentConfig)()
