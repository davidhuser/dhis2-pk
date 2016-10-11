# -*- coding: utf-8 -*-

from setuptools import setup

with open('LICENSE') as f:
    license = f.read()

setup(
    name='dhis2-pocket-knife',
    version='0.1',
    description='Tools for interacting with DHIS2 API in bulk',
    author='David Huser',
    author_email='dhuser@baosystems.com',
    url='https://github.com/davidhuser/DHIS2-API-tools',
    keywords='dhis2',
    license=license,
    install_requires=[
        "requests"
    ],
    scripts=[
        'scripts/delete-objects.py',
        'scripts/share-objects.py',
        'scripts/user-orgunits.py'
    ]
)