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
        'Flask==1.0.2',
        'requests==2.21.0',
        'pvl==0.3.0',
        'numpy==1.16.1',
        'matplotlib==3.0.2',
    ],
    license="BSD",
    zip_safe=False,
    keywords='web',
)
