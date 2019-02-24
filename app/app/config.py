import os
basedir = os.path.abspath(os.path.dirname(__file__))

PG_URI = 'postgresql://{name}:{password}@{image}:{port}/{name}'


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    ENV = 'dev'
    SECRET_KEY = 'iminthefuturealso'
    SQLALCHEMY_DATABASE_URI = PG_URI.format(
        name='perry',
        password='mypass',
        image='opp-database',
        port=5432,
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = PG_URI.format(
        name='testing',
        password='testpass',
        image='192.168.99.100',
        port=5432
    )
