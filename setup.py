#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from codecs import open
from shutil import rmtree

from setuptools import find_packages, setup, Command

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, 'src', '__version__.py'), 'r', 'utf-8') as f:
    exec(f.read(), about)


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

        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')

        sys.exit()


with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    keywords='dhis2',
    license='MIT',
    install_requires=[
        'dhis2.py==2.1.2'
    ],
    entry_points={
        'console_scripts': [
            'dhis2-pk = src.main:pocketknife_run',  # primary
            'dhis2-pk-indicator-definitions = src.main:pocketknife_run',  # legacy
            'dhis2-pk-share = src.main:pocketknife_run',
            'dhis2-pk-userinfo = src.main:pocketknife_run',
            'dhis2-pk-post-css = src.main:pocketknife_run',
            'dhis2-pk-attribute-setter = src.main:pocketknife_run',
            'dhis2-pk-validation-rules = src.main:pocketknife_run',
            'dhis2-pk-data-integrity = src.main:pocketknife_run'
        ]
    },
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    packages=find_packages(exclude=['tests']),
    test_suite='pytest',
    tests_require=['pytest'],
    setup_requires=['pytest-runner'],
    cmdclass={
        'publish': PublishCommand
    },
)
