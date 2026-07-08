"""Application configuration.

Kept as a single class for V1/V2 since we only run one environment locally.
A future version could add DevelopmentConfig/ProductionConfig subclasses.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    # Flask-SQLAlchemy looks for the SQLite file relative to the instance folder.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'flipiq.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
