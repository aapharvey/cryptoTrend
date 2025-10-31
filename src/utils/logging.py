from loguru import logger

def setup_logging():
    logger.remove()
    fmt = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    logger.add(lambda msg: print(msg, end=""), format=fmt, colorize=True, level="INFO")
    return logger
