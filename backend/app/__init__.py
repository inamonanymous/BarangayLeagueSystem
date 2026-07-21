from flask import Flask

from app.config import get_config
from app.extensions import init_extensions
from app.api.v1 import register_blueprints


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    init_extensions(app)
    register_blueprints(app)

    return app
