from .base import Config
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig


def get_config(name: str = "development"):
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    return configs.get(name, DevelopmentConfig)
