# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='dhis2-pocket-knife',
    version='0.0.1',
    description='Tools for interacting with DHIS2 API in bulk',
    author='David Huser',
    author_email='dhuser@baosystems.com',
    url='https://github.com/davidhuser/dhis2-pocket-knife',
    keywords='dhis2',
    install_requires=[
        "requests"
    ],
    scripts=[
        'scripts/delete-objects.py',
        'scripts/share-objects.py',
        'scripts/user-orgunits.py'
    ]
)
