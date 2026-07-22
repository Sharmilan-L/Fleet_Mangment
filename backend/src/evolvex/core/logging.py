import logging
import sys

from evolvex.core.config import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter ensuring consistent log structure across stdout.
    """

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", "-")
        record.message = record.getMessage()
        log_line = (
            f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}] "
            f"[{record.levelname}] "
            f"[req_id={request_id}] "
            f"[{record.name}]: {record.message}"
        )
        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"
        return log_line


def setup_logging() -> None:
    """
    Configures application-wide logging based on settings.LOG_LEVEL.
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(StructuredFormatter())

    root_logger.handlers = [handler]


logger = logging.getLogger("evolvex")
