# logger.py
import logging
import logging.config
import os

def setup_logger(log_file=None, level=logging.DEBUG, config=None):
    """
    Sets up the logger for the application.

    Parameters:
    - log_file: The file to which logs will be written. Overrides config if provided.
    - level: The logging level (e.g., logging.DEBUG, logging.INFO).
    - config: A dictionary containing logging configuration.

    Returns:
    - logger: Configured logger object.
    """
    if config:
        # If a log_file is specified outside of config, update it
        if log_file:
            # Update the file handler's filename
            if 'handlers' in config and 'file' in config['handlers']:
                config['handlers']['file']['filename'] = log_file
            else:
                raise ValueError("Logging config must have 'handlers' section with a 'file' handler.")

        # Ensure the log directory exists
        log_dir = os.path.dirname(log_file) if log_file else None
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
                print(f"Created log directory: {log_dir}")  # Debug statement
            except Exception as e:
                print(f"Failed to create log directory '{log_dir}': {e}")
                raise
        elif log_dir:
            print(f"Log directory already exists: {log_dir}")  # Debug statement

        # Configure logging using the provided config dictionary
        logging.config.dictConfig(config)
        logger = logging.getLogger('DroneLogger')
    else:
        logger = logging.getLogger('DroneLogger')
        logger.setLevel(level)

        # Avoid adding multiple handlers if logger already has them
        if not logger.handlers:
            # Ensure the directory for the log file exists
            if log_file:
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    try:
                        os.makedirs(log_dir, exist_ok=True)
                        print(f"Created log directory: {log_dir}")  # Debug statement
                    except Exception as e:
                        print(f"Failed to create log directory '{log_dir}': {e}")
                        raise
                    
            # Create console handler with a higher log level
            c_handler = logging.StreamHandler()
            c_handler.setLevel(logging.INFO)

            # Create file handler which logs even debug messages
            if log_file:
                try:
                    f_handler = logging.FileHandler(log_file)
                    print(f"Created file handler for log file: {log_file}")  # Debug statement
                except Exception as e:
                    print(f"Failed to create log file '{log_file}': {e}")
                    raise
                f_handler.setLevel(level)
            else:
                f_handler = None

            # Create formatters and add them to handlers
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            c_handler.setFormatter(formatter)
            if f_handler:
                f_handler.setFormatter(formatter)

                # Add the handlers to the logger
                logger.addHandler(c_handler)
                logger.addHandler(f_handler)
                print(f"Logger '{logger.name}' initialized with log file '{log_file}'")  # Debug statement
            else:
                logger.addHandler(c_handler)

    return logger
