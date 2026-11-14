from pathlib import Path
from logging.config import dictConfig
from src.config.app_config import settings

# Get root project directory (3 levels up from current file))
project_root = Path(__file__).parent.parent.parent
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

# Logging configuration
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': str(log_dir / 'app.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 3,
            'encoding': 'utf-8',
            'level': 'INFO'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': str(log_dir / 'error.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 3,
            'encoding': 'utf-8',
            'level': 'ERROR'
        }
    },
    'loggers': {
        '': {
            # If you have to write to app.log and error.log files
            'handlers': ['console', 'file', 'error_file'] if settings.write_logs_to_file else ['console'],
            'level': f'{settings.log_level}',
            'propagate': False
        },
        'grpc': {
            'level': 'ERROR',
            'propagate': False
        }
    }
}

def configure_logging():
    'Logging settings for the whole project'
    dictConfig(LOG_CONFIG)

# Automatic import configuration
configure_logging()
