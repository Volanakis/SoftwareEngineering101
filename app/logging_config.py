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

    if not app.logger.handlers:
        app.logger.addHandler(file_handler)
    else:
        app.logger.addHandler(file_handler)