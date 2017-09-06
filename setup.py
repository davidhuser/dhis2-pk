#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import io
from shutil import rmtree

from setuptools import find_packages, setup, Command

here = os.path.abspath(os.path.dirname(__file__))

__version__ = ''
with open(os.path.join('src', 'version.py')) as f:
    exec (f.read())


class PublishCommand(Command):
    """Support setup.py publish."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except (OSError, IOError):
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload dist/*')

        sys.exit()


class TestCommand(Command):
    description = 'Run Unit tests.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.status('Testing with pytest...')
        os.system('python -m pytest tests -sv')

# Import the README and use it as the long-description.
# Note: this will only work if 'README.rst' is present in your MANIFEST.in file!
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

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
        'requests>=2.4.2',
        'six',
        'unicodecsv>=0.14.1'
    ],
    entry_points={
        'console_scripts': [
            'dhis2-pk-indicator-definitions = src.scripts.indicator_definitions:main',
            'dhis2-pk-share-objects = src.scripts.share_objects:main',
            'dhis2-pk-metadata-dl = src.scripts.metadata_download:main',
            'dhis2-pk-userinfo = src.scripts.userinfo:main',
            'dhis2-pk-post-css = src.scripts.post_css:main'
        ]
    },
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ],
    packages=find_packages(exclude=['tests']),
    test_suite='pytest',
    tests_require=['pytest'],
    setup_requires=['pytest-runner'],
    cmdclass={
        'publish': PublishCommand,
        'test': TestCommand
    },
)
