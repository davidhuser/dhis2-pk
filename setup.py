# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages

__version__ = ''
with open(os.path.join('src', 'version.py')) as f:
    exec (f.read())

setup(
    name='dhis2-pocket-knife',
    version=__version__,
    description='Command-line tools for interacting with DHIS2 REST API',
    author='David Huser',
    author_email='dhuser@baosystems.com',
    url='https://github.com/davidhuser/dhis2-pocket-knife',
    keywords='dhis2',
    license='MIT',
    install_requires=[
        "requests>=2.4.2",
        "six>=1.10.0"
    ],
    scripts=[
        'src/scripts/dhis2-pk-share-objects',
        'src/scripts/dhis2-pk-user-orgunits',
        'src/scripts/dhis2-pk-indicator-definitions',
        'src/scripts/dhis2-pk-metadata-dl'
    ],
    packages=find_packages(exclude=['tests']),
    test_suite='pytest',
    tests_require=['pytest'],
    setup_requires=['pytest-runner']
)
