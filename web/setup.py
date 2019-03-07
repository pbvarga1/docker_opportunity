from setuptools import setup


setup(
    name='web',
    version='0.1.0',
    description='Opportunity Web app service',
    author='Perry Vargas',
    author_email='perrybvargas@gmail.com',
    packages=[
        'web',
    ],
    package_dir={'web':
                 'web'},
    include_package_data=True,
    install_requires=[
        'requests==2.21.0',
        'pvl==0.3.0',
        'numpy==1.16.2',
        'matplotlib==3.0.3',
        'redis==3.2.0',
        'Quart==0.8.1',
        'aiohttp==3.5.4',
        'aioredis==1.2.0',
        'sentry-sdk==0.7.6',
        'async-lru==1.0.2',
    ],
    license="BSD",
    zip_safe=False,
    keywords='web',
)
