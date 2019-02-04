# Copyright 2019 Luddite Labs Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os.path as op
from setuptools import setup

PY2 = sys.version_info[0] == 2


def get_version():
    with open('configsource.py') as f:
        for line in f:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])


def read(filename):
    return open(op.join(op.dirname(__file__), filename)).read()


tests_require = ['pytest', 'pytest-cov']

if PY2:
    tests_require += ['mock']


setup(
    name='configsource',
    version=get_version(),
    description='Simple configurations management for applications.',
    long_description=read('README.rst'),
    author='Sergey Kozlov',
    author_email='dev@ludditelabs.io',
    py_modules=['configsource'],
    install_requires=['future>=0.16.0'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],

    setup_requires=['pytest-runner'],
    tests_require=tests_require
)
