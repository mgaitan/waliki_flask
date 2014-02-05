#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)


#===============================================================================
# DOCS
#===============================================================================

"""This plugin versions your content into mercurial repository

Optional config:

    ``HG_REMOTE`` remote repository for pushin and pulling changes

"""

#===============================================================================
# IMPORTS
#===============================================================================

import os
import datetime

from flask import (Blueprint, render_template, current_app,
                   request, url_for, redirect, abort)
from flask.ext.script import Command

import hgapi


#===============================================================================
# CONSTANTS
#===============================================================================

PLUGIN_NAME = "waliki-hgplugin"


#===============================================================================
# BLUEPRINT
#===============================================================================

hgplugin = Blueprint(PLUGIN_NAME, __name__, template_folder='templates')


#===============================================================================
# SLOTS
#===============================================================================

def _msg(**kwargs):
    msg = kwargs.get("message") or "Autocommit of {}".format(PLUGIN_NAME)
    return msg


def hg_commit(page, **kwargs):
    msg = _msg(**kwargs)
    user = kwargs.get("user")
    if user:
        user = PLUGIN_NAME if user.is_anonymous() else user.name
    else:
        user = PLUGIN_NAME
    try:
        current_app.hg.hg_addremove()
        current_app.hg.hg_commit(msg, user)
    except hgapi.HgException as err:
        pass

#===============================================================================
#
#===============================================================================

class CmdHgSync(Command):
    """Execute secuencially: 'hg pull', 'hg update', 'hg addremove', 'hg commit' and 'hg push'"""

    def run(self):
        remote = current_app.config['HG_REMOTE']
        try:
            current_app.hg.hg_pull(remote)
        except hgapi.HgException as err:
            pass
        try:
            current_app.hg.hg_update("tip")
        except hgapi.HgException as err:
            pass
        try:
            current_app.hg.hg_addremove()
        except hgapi.HgException as err:
            pass
        try:
            current_app.hg.hg_commit(_msg(), PLUGIN_NAME)
        except hgapi.HgException as err:
            pass
        try:
            current_app.hg.hg_push(remote)
        except hgapi.HgException as err:
            pass


#===============================================================================
# INITS
#===============================================================================

REQUIREMENTS = ["hgapi"]


def init(app):
    # register plugin
    app.register_blueprint(hgplugin)

    # register signals
    app.signals.signal('page-saved').connect(hg_commit)

    # add cli commands
    app.manager.add_command("hgsync", CmdHgSync())

    # init repository
    app.hg = hgapi.Repo(app.config['CONTENT_DIR'])
    try:
        app.hg.hg_init()
    except hgapi.HgException as err:
        pass


#===============================================================================
# MAIN
#===============================================================================

if __name__ == "__main__":
    print(__doc__)

