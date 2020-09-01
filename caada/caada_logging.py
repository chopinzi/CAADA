import logging

logger = logging.getLogger('CAADA')
formatter = logging.Formatter('[%(levelname)s - %(module)s] %(message)s')
stream = logging.StreamHandler()
stream.setFormatter(formatter)
logger.addHandler(stream)
logger.setLevel(logging.DEBUG)  # default to highest logging


def set_log_level(level):
    # Assumes that level = 1 is the normal level of operation which prints information messages
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logger.setLevel(levels[level])
