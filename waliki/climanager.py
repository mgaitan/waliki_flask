#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)

#===============================================================================
# DOCS
#===============================================================================

"""Script manager for waliki

"""

#===============================================================================
# IMPORTS
#===============================================================================

import codecs
import os
import random
import hashlib
import time

from flask.ext import script

from . import core


#===============================================================================
# MANAGER
#===============================================================================

manager = script.Manager(core.app)


#===============================================================================
# CONSTANTS
#===============================================================================

CONFIG_TEMPLATE_VARS = u"""
# encoding: utf-8

# Title of the wiki
TITLE = '{{title}}'

# Don't show this to anybody
SECRET_KEY = '{{secret_key}}'

# The extensions are the name of the files inside 'extension folder'
EXTENSIONS = [
    {% for ext in extensions %}
    'ext'
    {% endfor %}
]

# restructuredtext or markdown
MARKUP = '{{ markup }}'


# PERMISSIONS can be:
#   public: everybody can read and write a page (default)
#   protected: anyone can view but only registered users can write
#   secure: only registered users can see this wiki
#   private: all the users are created inactive
PERMISSIONS = '{{permissions}}'

# Can be HTML
CUSTOM_FOOTER = 'Powered by <a href="http://waliki.nqnwebs.com/"> Waliki</a>'

# This logo is show on the left side of te title
NAV_BAR_ICON = '{{navbar_icon}}'

# In 16x16 px .ico format
FAVICON = '{{favicon}}'

# Used as base theme (Bootstrap 2.x)
# amelia, cosmo, cyborg, slate, cerulean, flatly, journal, readable, simplex,
# united, spacelab
{-% if bootswatch %}
# BOOTSWATCH_THEME = 'simplex'
{-% else %}
BOOTSWATCH_THEME = '{{bootswatch}}'
{-% endif %}

# The custom css is the last one to be aplied to the style
CUSTOM_CSS = '{{custom_css}}'
"""

CONFIG_OPTIONS = (
    {
        "var": "title",
        "prompt": "Wiki Tittle",
        "default": lambda bn, fp: u"{} Wiki".format(bn.title()),
        "validator": lambda v: True,
    },
    {
        "var": "secret_key",
        "no_prompt": True,
        "default": lambda bn, fp: make_secret_key(),
    },
    {
        "var": "markup",
        "prompt": "Choice the markup (markdown|restructuredtext)",
        "default": lambda bn, fp: "restructuredtext",
        "validator": lambda v: v in ("restructuredtext", "markdown")
    },
    {
        "var": "permissions",
        "prompt": "Choice the permissions level (public|protected|secure|private)",
        "default": lambda bn, fp: "public",
        "validator": lambda v: v in ("public", "protected", "secure", "private")
    },
    {
        "var": "navbar_icon",
        "no_prompt": True,
        "default": lambda bn, fp: os.path.join(fp, "res", "logo.png"),
    },
    {
        "var": "favicon",
        "no_prompt": True,
        "default": lambda bn, fp: os.path.join(fp, "res", "favicon.ico"),
    },
    {
        "var": "bootswatch",
        "prompt": "Bootswatch base css (amelia|cosmo|cyborg|slate|cerulean|flatly|journal|readable|simplex|united|spacelab)",
        "default": lambda bn, fp: None,
        "validator": lambda v: v in ("amelia", "cosmo", "cyborg", "slate",
                                     "cerulean", "flatly", "journal",
                                     "readable", "simplex", "united",
                                     "spacelab")
    },
    {
        "var": "custom_css",
        "no_prompt": True,
        "default": lambda bn, fp: os.path.join(fp, "res", "waliki.css"),
    },


)

#===============================================================================
# COMMANDS
#===============================================================================

@manager.command
def create_wiki(dest):
    """Create a configuration file and a wsgi for a new wiki"""
    basename = os.path.basename(dest)
    fulldest = dest if os.path.isabs(dest) else os.path.abspath(dest)

    print ("Welcome to the Waliki wiki creation utility.\n"
           "\n"
           "Please enter values for the following settings (just press Enter\n"
           "to accept a default value, if one is given in brackets).\n")
    context = {}
    for option in CONFIG_OPTIONS:
        var = option["var"]
        default = option["default"](basename, fulldest)
        if option.get("no_prompt"):
            value = default
        else:
            prompt = option["prompt"]
            value = raw_input("{} [{}]: ".format(prompt, default))
            if not value:
                value = default
            else:
                validator = option["validator"]
                while not validator(value):
                    print u"The value '{}' is invalid".format(value)
                    value = raw_input("{} [{}]: ".format(prompt, default))
                    if not value:
                        value = default
                        break
        context[var] = value

    extensions = []
    print "\nExtensions:"
    for ext in core.EXTENSIONS:
        enable = raw_input("Enable '{}'? [No]:  ".format(ext))
        if enable:
            while enable.lower() not in ("yes", "no"):
                enable = raw_input("Please write 'yes', 'no' or empty :")
            if enable.lower() == "yes":
                extensions.append(ext)
    context["extensions"] = extensions




#===============================================================================
# FUNCTIONS
#===============================================================================

def make_secret_key():
    buff = []

    chars = list("!|#$%&/¿?+*@-_abcdefghijklmnopqrtsuvwxyz")
    for idx in range(10):
        buff.append(random.choice(chars))

    seed = str(random.random())
    buff += list(hashlib.sha1(seed).hexdigest())

    buff += list(str(time.time()))


    for idx, char in  enumerate(buff):
        if random.choice([True, False]):
            char = char.upper()
        buff[idx] = char

    random.shuffle(buff)

    return "".join(buff)


#===============================================================================
# MAIN
#===============================================================================

if __name__ == "__main__":
    print(__doc__)
