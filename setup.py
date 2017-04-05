# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

__VERSION__ = '0.5.0'

setup(
    name='dhis2-pocket-knife',
    version=__VERSION__,
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
        'src/scripts/dhis2-pk-indicator-definitions'
    ],
    packages=find_packages(exclude=['tests']),
    test_suite='pytest',
    tests_require=['pytest'],
    setup_requires=['pytest-runner']
)
