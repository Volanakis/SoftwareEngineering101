import logging
import os

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_MARKER = "_cinema_app_handler"


def configure_logging(app):
    level = logging.DEBUG if app.debug else logging.INFO

    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)
    app.logger.setLevel(level)

    if _has_marked_handler(app_logger):
        return

    formatter = logging.Formatter(_FORMAT)

    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler(
        os.path.join("logs", "app.log"), encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    setattr(file_handler, _MARKER, True)
    app_logger.addHandler(file_handler)

    if app.debug:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(level)
        setattr(stream_handler, _MARKER, True)
        app_logger.addHandler(stream_handler)


def _has_marked_handler(logger):
    return any(getattr(handler, _MARKER, False) for handler in logger.handlers)
