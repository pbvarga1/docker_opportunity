from setuptools import setup


setup(
    name='app',
    version='0.1.0',
    description='Opportunity database app service',
    author='Perry Vargas',
    author_email='perrybvargas@gmail.com',
    packages=[
        'app',
    ],
    package_dir={'app':
                 'app'},
    include_package_data=True,
    install_requires=[
        'Flask==1.0.2',
        'requests==2.21.0',
        'SQLAlchemy==1.2.18',
        'Flask-SQLAlchemy==2.3.2',
        'psycopg2-binary==2.7.7',
    ],
    license="BSD",
    zip_safe=False,
    keywords='app',
)
