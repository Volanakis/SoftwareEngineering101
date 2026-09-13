import logging
import os


def configure_logging(app):
    os.makedirs("logs", exist_ok=True)

    log_file = os.path.join("logs", "app.log")

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    app.logger.setLevel(logging.INFO)

    absolute_log_file = os.path.abspath(log_file)
    has_file_handler = any(
        isinstance(handler, logging.FileHandler)
        and handler.baseFilename == absolute_log_file
        for handler in app.logger.handlers
    )

    if not has_file_handler:
        app.logger.addHandler(file_handler)
    else:
        file_handler.close()
