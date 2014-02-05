#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)

#===============================================================================
# DOCS
#===============================================================================

"""Waliki is an extensible wiki engine based on Flask.

:home: https://github.com/mgaitan/waliki/
:documentation: http://waliki.rtfd.org (under development)
:demo: http://waliki.nqnwebs.com
:discussion group: https://groups.google.com/forum/#!forum/waliki-devs
:license: `BSD <https://github.com/mgaitan/waliki/blob/master/LICENSE>`_

At a glance, Waliki has:

- File based content. No database is required (but optional)
- An extensible architecture: almost everything is a plugin
- version control for your content using git or mercurial
- markdown or reStructuredText support
- simple caching
- UI based on bootstrap

"""

PRJ = "Waliki"

VERSION = ("0", "2", "dev")

STR_VERSION = ".".join(VERSION)

DESCRIPTION = __doc__

SHORT_DESCRIPTION = DESCRIPTION.splitlines()[0].strip()

AUTHOR = "Martín Gaitan"

EMAIL = "gaitan@gmail.com"

URL = "http://waliki.nqnwebs.com/"

LICENSE = "BSD"

KEYWORDS = "wiki restructuredtext markdown"

CLASSIFIERS = (
    "Topic :: Utilities",
    "License :: OSI Approved :: BSD License",
    "Programming Language :: Python :: 2",
)


#===============================================================================
# FUNCTIONS
#===============================================================================

def get_manager(load_config):
    """Returns the waliki script manager.

    :param load_config: if True try to load the config from enviroment

    """
    if load_config:
        from . import app
    from . import climanager
    return climanager.manager


def run(load_config=False):
    """Runs waliki.

    :param load_config: if True try to load the config from enviroment

    """
    manager = get_manager(load_config)
    manager.run()


def get_app(load_config):
    """Returns waliki application

    :param load_config: if True try to load the config from enviroment

    """
    if load_config:
        from . import app
    from .import core
    return core.app

#===============================================================================
# MAIN
#===============================================================================

if __name__ == "__main__":
    print(__doc__)
