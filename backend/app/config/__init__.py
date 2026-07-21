from .base import Config
from .development import DevelopmentConfig
from .production import ProductionConfig


def get_config(name: str = "development"):
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    return configs.get(name, DevelopmentConfig)
