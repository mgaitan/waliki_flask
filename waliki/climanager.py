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
import codecs

import jinja2

from flask.ext import script

from . import core


#===============================================================================
# MANAGER
#===============================================================================

manager = script.Manager(core.app)


#===============================================================================
# CONSTANTS
#===============================================================================

WALIKI_FILENAME = "waliki.py"

WALIKI_TEMPLATE = jinja2.Template(u"""#!/usr/bin/env python
import os
import sys

CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "config.py"
)

if __name__ == "__main__":
    os.environ.setdefault("WALIKI_CONFIG_MODULE", CONFIG_PATH)
    from waliki.app import app
    app.manager.run()
""")


CONFIG_FILENAME = "config.py"

CONFIG_TEMPLATE = jinja2.Template(u"""# encoding: utf-8

# Title of the wiki
TITLE = '{{title}}'

# Don't show this to anybody
SECRET_KEY = '{{secret_key}}'

# The extensions are the name of the files inside 'extension folder'
EXTENSIONS = (
    {%- for ext in extensions %}
    '{{ext}}'
    {%- endfor %}
)

# DATADIR
DATA_DIR = '{{datadir}}'

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
{%- if bootswatch %}
# BOOTSWATCH_THEME = 'simplex'
{%- else %}
BOOTSWATCH_THEME = '{{bootswatch}}'
{%- endif %}

# The custom css is the last one to be aplied to the style
CUSTOM_CSS = '{{custom_css}}'

""")

REQUIREMENTS_FILE = "requirements.txt"

REQUIREMENTS_TEMPLATE = jinja2.Template("""
{%- for r in requirements %}
{{r}}
{%- endfor %}
""".strip())

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
        "var": "data_dir",
        "prompt": "The name of the directory to store your pages",
        "default": lambda bn, fp: "_data",
        "validator": lambda v: os.path.sep not in v
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
    config_context = {}
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
        try:
            config_context[var] = unicode(value) if value else value
        except Exception as err:
            import ipdb; ipdb.set_trace()

    extensions = []
    requirements = []
    print "\nExtensions:"
    for ext in core.EXTENSIONS:
        enable = raw_input("Enable '{}'? [No]:  ".format(ext))
        if enable:
            while enable.lower() not in ("yes", "no"):
                enable = raw_input("Please write 'yes', 'no' or empty :")
            if enable.lower() == "yes":
                extensions.append(ext)
                requirements.extend(core.get_extension_requirements(ext))
    config_context["extensions"] = extensions

    os.makedirs(fulldest)

    config_fpath = os.path.join(fulldest, CONFIG_FILENAME)
    with codecs.open(config_fpath, "w", encoding="utf8") as fp:
        fp.write(CONFIG_TEMPLATE.render(config_context))
    requirements_fpath = os.path.join(fulldest, REQUIREMENTS_FILE)
    with codecs.open(requirements_fpath, "w", encoding="utf8") as fp:
        fp.write(REQUIREMENTS_TEMPLATE.render(requirements=requirements))

    print("Your Wiki is ready!")






#===============================================================================
# FUNCTIONS
#===============================================================================

def make_secret_key():
    buff = []

    chars = list("+-*?!~@abcdefghijklmnopqrtsuvwxyz")
    for idx in range(10):
        buff.append(random.choice(chars))

    seed = str(random.random())
    buff += list(hashlib.sha1(seed).hexdigest())

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
