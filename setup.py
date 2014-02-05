#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)


#===============================================================================
# DOCS
#===============================================================================

"""This file is for distribute waliki with distutils

"""


#===============================================================================
# IMPORTS
#===============================================================================

import sys, os

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

import waliki


#===============================================================================
# CONSTANTS
#===============================================================================

PATH = os.path.abspath(os.path.dirname(__file__))

REQUIREMENTS_PATH = os.path.join(PATH, "requirements.txt")

with open(REQUIREMENTS_PATH) as fp:
    REQUIREMENTS =  fp.read().splitlines()


#===============================================================================
# FUNCTIONS
#===============================================================================

setup(
    name=waliki.PRJ.lower(),
    version=waliki.STR_VERSION,
    description=waliki.SHORT_DESCRIPTION,
    author=waliki.AUTHOR,
    author_email=waliki.EMAIL,
    url=waliki.URL,
    license=waliki.LICENSE,
    keywords=waliki.KEYWORDS,
    classifiers=waliki.CLASSIFIERS,
    packages=[pkg for pkg in find_packages() if pkg.startswith("waliki")],
    include_package_data=True,
    py_modules=["ez_setup"],
    entry_points={'console_scripts': ['waliki-admin = waliki:run']},
    install_requires=REQUIREMENTS,
)
