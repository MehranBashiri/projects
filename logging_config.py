import logging
import logging.config

def setup_logging():
    """
    Sets up logging configuration for the application.
    """
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,  # Do not disable other loggers
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
            'verbose': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]',
            },
        },
        'handlers': {
            'console': {
                'level': 'WARNING',  # Only WARNING and above messages will appear in the console
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
            'file': {
                'level': 'INFO',  # Log INFO and above messages to the file
                'class': 'logging.FileHandler',
                'filename': 'application.log',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': 'INFO',  # Set the root logger level to INFO
                'propagate': True,
            },
            'visualization': {  # Custom logger for visualization.py
                'handlers': ['console', 'file'],
                'level': 'INFO',  # Set the specific level for this module's logger
                'propagate': False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
    logging.info("Logging setup complete.")
