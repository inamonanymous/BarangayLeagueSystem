from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session


db = SQLAlchemy()
migrate = Migrate()
session = Session()


def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    session.init_app(app)
