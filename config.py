import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///cinema.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ΜΛΑ-3.3: rate limiting. In-memory storage is fine for dev/single-process;
    # point RATELIMIT_STORAGE_URI at redis://... in production for a shared store.
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    # Disabled by default so the shared in-process limiter state cannot make
    # unrelated tests flaky; test_rate_limiting.py re-enables it explicitly.
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    pass


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
