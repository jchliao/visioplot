import logging


LOGGER = logging.getLogger("visioplot")

if not LOGGER.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    LOGGER.addHandler(_handler)

LOGGER.setLevel(logging.WARNING)
LOGGER.propagate = False


def set_debug(enabled: bool = True):
    """Enable or disable debug-level logs for visioplot."""
    LOGGER.setLevel(logging.DEBUG if enabled else logging.WARNING)


def debug_print(message: str):
    """Debug log helper used instead of raw print in library internals."""
    LOGGER.debug(message)


def warn_print(message: str):
    """Warning log helper for recoverable issues."""
    LOGGER.warning(message)


def error_print(message: str):
    """Error log helper for failure reporting."""
    LOGGER.error(message)
