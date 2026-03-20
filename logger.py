import logging

from rich.console import Console
from rich.logging import RichHandler

console = Console(force_terminal=True, soft_wrap=True, stderr=True)

LEVEL_COLORS = {
    logging.DEBUG: "dim",
    logging.INFO: "green",
    logging.WARNING: "yellow",
    logging.ERROR: "red",
    logging.CRITICAL: "bold red",
}


class ColoredRichHandler(RichHandler):
    """RichHandler that colors the entire message based on log level."""

    def emit(self, record: logging.LogRecord) -> None:
        color = LEVEL_COLORS.get(record.levelno, "")
        if color:
            record.msg = f"[{color}]{record.msg}[/{color}]"
        super().emit(record)


handler = ColoredRichHandler(
    console=console,
    show_time=True,
    show_path=False,
    rich_tracebacks=True,
    markup=True,
)

logger = logging.getLogger("ekantipur")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

__all__ = ["logger"]
