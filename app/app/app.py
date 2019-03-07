from typing import Dict, Any

from datetime import datetime

import sentry_sdk
from flask import Flask
import sqlalchemy as sa  # type: ignore
from flask_cors import CORS  # type: ignore
from flask_sqlalchemy import SQLAlchemy, Model  # type: ignore
from sentry_sdk.integrations.flask import FlaskIntegration

from app import config
from app.constants import DSN

sentry_sdk.init(
    dsn=DSN,
    integrations=[FlaskIntegration()]
)

app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)  # type: ignore
app.url_map.strict_slashes = False
CORS(app)


class Base(Model):
    ID = sa.Column(sa.Integer, primary_key=True)
    Active = sa.Column(sa.Boolean, default=True)
    Created = sa.Column(
        sa.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    Updated = sa.Column(
        sa.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self):
        return f'{self.__class__.__name__}({self.ID})'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ID': self.ID,
            'Created': self.Created.isoformat(),
            'Updated': self.Updated.isoformat(),
            'Active': self.Active,
        }

    @classmethod
    def from_dict(cls, model_dict: Dict[str, Any]):
        raise NotImplementedError('from_dict not implemented')

    def update_from_dict(self, model_dict: Dict[str, Any]) -> None:
        if 'Active' in model_dict and model_dict['Active'] is True:
            self.Active = True

    def delete(self) -> None:
        self.Active = False


db = SQLAlchemy(app, model_class=Base)
