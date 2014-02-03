#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)


#===============================================================================
# DOCS
#===============================================================================

"""Cache plugin

"""

#===============================================================================
# IMPORTS
#===============================================================================

from flask.ext.cache import Cache


#===============================================================================
# INITIALIZATION
#===============================================================================

def init():
    pass

cache = Cache()
