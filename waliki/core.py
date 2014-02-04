#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)

#===============================================================================
# DOCS
#===============================================================================

"""This module contains only the flask application

"""

#===============================================================================
# IMPORTS
#===============================================================================

import os

import flask

#===============================================================================
# CONSTANTS
#===============================================================================

WALIKI_PATH = os.path.abspath(os.path.dirname(__file__))

EXTENSIONS_PATH = os.path.join(WALIKI_PATH, "extensions")

EXTENSIONS = frozenset(
    os.path.splitext(mn)[0]
    for mn in os.listdir(EXTENSIONS_PATH) if not mn.startswith("_")
)

#===============================================================================
# APP
#===============================================================================

app = flask.Flask(__name__)


#===============================================================================
# MAIN
#===============================================================================

if __name__ == "__main__":
    print(__doc__)
