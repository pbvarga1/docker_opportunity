from datetime import datetime

from flask import Flask
import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy, Model

from app import config

app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)
app.url_map.strict_slashes = False


class Base(Model):
    ID = sa.Column(sa.Integer, primary_key=True)
    Active = sa.Column(sa.Boolean, default=True)
    Created = sa.Column(
        sa.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    Updated = sa.Column(sa.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'{self.__class.__name__}({self.ID})'

    def to_dict(self):
        return {
            'ID': self.ID,
            'Created': str(self.Created),
            'Updated': str(self.Updated),
            'Active': self.Active,
        }

    @classmethod
    def from_dict(cls, model_dict):
        raise NotImplementedError('from_dict not implemented')

    def update_from_dict(self, model_dict):
        if 'Active' in model_dict and model_dict['Active'] is True:
            self.Active = True

    def delete(self):
        self.Active = False


db = SQLAlchemy(app, model_class=Base)
