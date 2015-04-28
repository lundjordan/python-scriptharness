#!/usr/bin/env python
"""
setup.py for scriptharness
"""
# TODO use versioneer?

from setuptools import setup, find_packages
import sys

import scriptharness

dependencies = [
    'six',
]

# TODO verify we can run in 2.6!
if sys.version_info < (2, 6):
    print('ERROR: scriptharness requires Python 2.6 or above! Exiting...')
    sys.exit(1)
elif sys.version_info < (2, 7):
    dependencies.append('argparse')

setup(
    name='scriptharness',
    version=scriptharness.__version_string__,
    description='A generic logging, configuration, and workflow harness for scripts.',
    author='Aki Sasaki',
    author_email='aki@escapewindow.com',
    url='https://github.com/escapewindow/scriptharness',
    license='MPL2',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
    entry_points="""
# -*- Entry points: -*-
""",
)
