# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='Flask-Session',
    version='0.1.0',
    url='https://github.com/codehugger/Flask-Session.git',
    license='BSD',
    author='Bjarki Gudlaugsson',
    author_email='bjarki@codehuggers.com',
    description='Redis session interface extension for Flask',
    long_description=__doc__,
    py_modules=['flask_session'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'redis'
    ]
)
