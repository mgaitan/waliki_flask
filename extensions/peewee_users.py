#!/usr/bin/env python
# -*- coding: utf-8 -*-

#===============================================================================
# DOCS
#===============================================================================

"""This plugin store all user data in peewee database

"""

#===============================================================================
# IMPORTS
#===============================================================================

import os
import datetime
try:
    import cPickle as pickle
except ImportError:
    import pickle

from flask import (Blueprint, render_template, current_app,
                   request, url_for, redirect, abort)
from flask.ext.script import Command

import peewee
from flask_peewee.db import Database


#===============================================================================
# CONSTANTS
#===============================================================================

PLUGIN_NAME = "waliki-peewee_usersplugin"

DATABASE_PROXY = peewee.Proxy()

#===============================================================================
# BLUEPRINT
#===============================================================================

peewee_user_plugin = Blueprint(PLUGIN_NAME, __name__,
                               template_folder='templates')

#===============================================================================
# MODELS
#===============================================================================

class User(peewee.Model):
    name = peewee.CharField(index=True)
    full_name = peewee.CharField()
    email = peewee.CharField()
    password = peewee.CharField(max_length=300)
    authentication_method = peewee.CharField()
    active = peewee.BooleanField()
    authenticated  = peewee.BooleanField()
    _roles = peewee.TextField(db_column="roles_pkl_b64")

    class Meta:
        database = DATABASE_PROXY
        db_table = "waliki_users"

    def save(self, *args, **kwargs):
        if hasattr(self, "_roles_buff"):
            self._roles = pickle.dumps(self._roles_buff).encode("base64")
        super(User, self).save(*args, **kwargs)

    @property
    def roles(self):
        if not hasattr(self, "_roles_buff"):
            if self._roles:
                self._roles_buff = pickle.loads(self._roles.decode("base64"))
            else:
                self._roles_buff = []
        return self._roles_buff

    @roles.setter
    def roles(self, rs):
        self._roles_buff = rs




#===============================================================================
# WRAPPER
#===============================================================================

class PeeweeFlaskLoginUserWrapper(object):

    def __init__(self, pu):
        self.pu = pu

    def __getattr__(self, n):
        return getattr(self.pu, n)

    def get(self, option):
        return getattr(self.pu, option, None)

    def set(self, option, value):
        setattr(self.pu, option, value)
        self.save()

    def is_authenticated(self):
        return self.pu.authenticated

    def is_active(self):
        return self.pu.active

    def is_anonymous(self):
        return False

    def check_password(self, password):
        return current_app.check_password(self.pu.authentication_method,
                                          self.pu.password, password)

    def get_id(self):
        return self.pu.name

    def save(self, *args, **kwargs):
        self.pu.save()


#===============================================================================
# PLUGIN
#===============================================================================

class PeeweeUsersManager(object):

    def add_user(self, name, password, full_name, email,
                 active=True, roles=[], authentication_method=None):
        user = User()
        user.name = name
        user.password = current_app.make_password(authentication_method, password)
        user.full_name = full_name
        user.active = active
        user.authentication_method = authentication_method
        user.authenticated = False
        user.email = email
        user.roles = roles
        user.save()

        return PeeweeFlaskLoginUserWrapper(user)

    def get_user(self, name):
        query = User.select().where(User.name == name)
        if query.count():
            return PeeweeFlaskLoginUserWrapper(query[0])

    def delete_user(self, name):
        query = User.delete().where(User.name == name)
        return bool(query.execute())

    def update(self, name, userdata):
        User.update(**userdata).where(User.name == name)

#===============================================================================
# COMMAND
#===============================================================================

class CMDImportJSONUsers(Command):
    """Copy all data from stored  JSON to database"""

    def __init__(self, datasource):
        super(CMDImportJSONUsers, self).__init__()
        self.datasource = datasource

    def run(self):
        for uname, udata in self.datasource.read().items():
            #roles = udata.pop("roles")
            if "hash" in udata:
                udata["password"] = udata["hash"]
                udata.pop("hash")
            udata["name"] = uname
            user = User(**udata)
            user.save()

#===============================================================================
# INITS
#===============================================================================

def init(app):
    app.register_blueprint(peewee_user_plugin)
    db = Database(app)
    DATABASE_PROXY.initialize(db.database)
    User.create_table(True)

    # add cli commands
    app.manager.add_command(
        "import-json-users", CMDImportJSONUsers(app.users)
    )

    app.users = PeeweeUsersManager()


#===============================================================================
# MAIN
#===============================================================================

if __name__ == "__main__":
    print(__doc__)

