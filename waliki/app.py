#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)

#===============================================================================
# DOCS
#===============================================================================

"""Waliki itself!

"""


#===============================================================================
# IMPORTS
#===============================================================================

import os
import re

from functools import wraps
from flask import (render_template, flash, redirect, url_for, request,
                   send_from_directory)
from flask.ext.login import (LoginManager, login_required, current_user,
                             login_user, logout_user)
from flask.ext.wtf import Form
from wtforms import (TextField, TextAreaField, PasswordField, HiddenField)
from wtforms.validators import (Required, ValidationError, Email)

from wiki import Wiki
from users import (UserManager, check_password, make_password,
                  get_default_authentication_method)
import markup
from extensions.cache import cache
from signals import wiki_signals, page_saved, pre_display, pre_edit
from . import core
from .climanager import manager


#===============================================================================
# PATCH FOR BACK COMPATIBILITY
#===============================================================================

app = core.app


#===============================================================================
# CONSTANTS
#===============================================================================

CONFIG_FILE_PATH = os.environ.get("WALIKI_CONFIG_MODULE")

CUSTOM_STATICS_DIR_NAME = "_custom"

CUSTOM_STATICS_LIST = ["NAV_BAR_ICON", "FAVICON", "CUSTOM_CSS"]

PERMISSIONS_PUBLIC = "public"
PERMISSIONS_PROTECTED = "protected"
PERMISSIONS_SECURE = "secure"
PERMISSIONS_PRIVATE = "private"
DEFAULT_PERMISSIONS = PERMISSIONS_PUBLIC


#===============================================================================
# THE CODE
#===============================================================================

def user_can_edit(can_modify=True):
    pers = app.config.get("PERMISSIONS", DEFAULT_PERMISSIONS)
    if pers == PERMISSIONS_PUBLIC:
        return True
    elif pers == PERMISSIONS_PROTECTED:
        if can_modify and not current_user.is_authenticated():
            return False
    elif pers in (PERMISSIONS_SECURE, PERMISSIONS_PRIVATE):
        if not current_user.is_authenticated():
            return False
    return True


def protect(can_modify):
    """If can_modify is True this view can modify the wiky"""
    def _dec(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not user_can_edit(can_modify):
                return app.loginmanager.unauthorized()
            return f(*args, **kwargs)
        return wrapper
    return _dec


#===============================================================================
# FORMS
#===============================================================================

class ForbiddenUrlError(ValueError):

    def __init__(self, invalidpart, url):
        self.invalidpart = invalidpart
        self.url = url
        super(ForbiddenUrlError, self).__init__(
            "You can't create a page inside '{0}': {1}".format(invalidpart, url)
        )

    @property
    def redirect(self):
        if self.invalidpart.startswith("_"):
            idx = self.url.index(self.invalidpart)
            return "/" + self.url[:idx]
        return self.invalidpart


def urlify(url, protect_specials_url=True):
    # Cleans the url and corrects various errors.
    # Remove multiple spaces and leading and trailing spaces
    if protect_specials_url:
        if re.match(r'^(?i)(user|tag|create|search|index)', url):
            invalid = url.replace('\\\\', '/').replace('\\', '/').split("/", 1)[0]
            raise ForbiddenUrlError(invalid, url)
        for p in url.replace('\\\\', '/').replace('\\', '/').split("/"):
            if p in ("_edit"):
                raise ForbiddenUrlError(p, url)

    pretty_url = re.sub('[ ]{2,}', ' ', url).strip()
    pretty_url = pretty_url.lower().replace('_', '-').replace(' ', '-')
    # Corrects Windows style folders
    pretty_url = pretty_url.replace('\\\\', '/').replace('\\', '/')
    return pretty_url


class URLForm(Form):
    url = TextField('', [Required()])

    def validate_url(form, field):
        if wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        return urlify(url)


class SearchForm(Form):
    term = TextField('', [Required()])


class EditorForm(Form):
    title = TextField('', [Required()])
    body = TextAreaField('', [Required()])
    tags = TextField('')
    message = TextField('')
    checksum = HiddenField()


class LoginForm(Form):
    name = TextField('Username', [Required()])
    password = PasswordField('Password', [Required()])

    def validate_name(form, field):
        user = app.users.get_user(field.data)
        if not user:
            raise ValidationError('This username does not exist.')

    def validate_password(form, field):
        user = app.users.get_user(form.name.data)
        if not user:
            return
        if not user.check_password(field.data):
            raise ValidationError('Username and password do not match.')


class SignupForm(Form):
    name = TextField('Username', [Required()])
    email = TextField('Email', [Required(), Email()])
    full_name = TextField('Full name')
    password = PasswordField('Password', [Required()])

    def validate_name(form, field):
        user = app.users.get_user(field.data)
        if user:
            raise ValidationError('This username is already taken')

    def validate_password(form, field):
        if len(field.data) < 4:
            raise ValidationError('The password is too short')


#===============================================================================
# APPLICATION SETUP
#===============================================================================

app.debug = True
try:
    app.config.from_pyfile(CONFIG_FILE_PATH)
except IOError:
    print ("Enviroment variable 'WALIKI_CONFIG_MODULE' not found")
    sys.exit(1)

app.config['CONTENT_DIR'] = os.path.join(app.config['DATA_DIR'], "content")
app.config['CACHE_DIR'] = os.path.join(app.config['DATA_DIR'], "cache")
app.config['WIKI_ROOT'] = os.path.dirname(CONFIG_FILE_PATH)
app.config['EDITOR_THEME'] = 'monokai'
app.config['CUSTOM_STATICS_DIR_NAME'] = CUSTOM_STATICS_DIR_NAME
app.config['CUSTOM_STATICS'] = {}


cache.init_app(app, config={'CACHE_TYPE': 'filesystem',
                            'CACHE_DIR': app.config["CACHE_DIR"]})
loginmanager = LoginManager()
loginmanager.init_app(app)
loginmanager.login_view = 'user_login'
markup = dict([(klass.NAME, klass) for klass in
               markup.Markup.__subclasses__()])[app.config.get('MARKUP')]

wiki = Wiki(app.config.get('CONTENT_DIR'), markup)

# FIX ME: This monkeypatching is pollution crap .
#         Should be possible to import them wherever,
#         Wiki class should be a singleton.
app.wiki = wiki
app.signals = wiki_signals
app.EditorForm = EditorForm
app.loginmanager = loginmanager
app.manager = manager
app.users = UserManager(app.config.get('DATA_DIR'), app)
app.check_password = check_password
app.make_password = make_password

app.jinja_env.globals.update(user_can_edit=user_can_edit)

#===============================================================================
# VARIABLE STATIC FILE
#===============================================================================

for cs in CUSTOM_STATICS_LIST:
    csvalue = app.config.get(cs)
    if csvalue:
        csbasename = os.path.basename(csvalue)
        cspath = (csvalue if os.path.isabs(cs) else
                  os.path.join(app.config["WIKI_ROOT"], csvalue))
        app.config['CUSTOM_STATICS'][csbasename] = os.path.dirname(cspath)
        app.config[cs] = csbasename


#===============================================================================
# ROUTES
#===============================================================================

@loginmanager.user_loader
def load_user(name):
    return app.users.get_user(name)


"""
    Routes
    ~~~~~~
"""


@app.route('/custom_static/<path:filename>')
def custom_static(filename):
    path = app.config["CUSTOM_STATICS"][filename]
    return send_from_directory(path, filename)


@app.route('/')
@protect(False)
def home():
    page = wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@app.route('/index/')
@protect(False)
def index():
    pages = wiki.index()
    return render_template('index.html', pages=pages)


@app.route('/<path:url>/')
@protect(False)
def display(url):
    page = wiki.get(url)
    if not page:
        try:
            pretyurl = urlify(url)
        except ForbiddenUrlError as err:
            flash(err.message, 'error')
            if "/" in err.redirect:
                return redirect(err.redirect)
            return redirect(url_for(err.redirect))
        else:
            flash('The page "{0}" does not exist, '
                  'feel free to make it now!'.format((url)), 'warning')
            return redirect(url_for('edit', url=pretyurl))
    extra_context = {}
    pre_display.send(page, user=current_user, extra_context=extra_context)
    return render_template('page.html', page=page, **extra_context)


@app.route('/create/', methods=['GET', 'POST'])
@protect(True)
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for('edit', url=urlify(form.url.data)))
    return render_template('create.html', form=form)


@app.route('/<path:url>/_edit', methods=['GET', 'POST'])
@protect(True)
def edit(url):
    page = wiki.get(url)
    form = EditorForm(obj=page)
    checksum = page.checksum if page else ""
    conflict = None
    if form.validate_on_submit():
        if checksum != form.checksum.data:
            flash('The document are chaged see the new version in the upper frame',
                  'error')
            conflict = render_template('page.html', page=page)
        else:
            if not page:
                page = wiki.get_bare(url)
            form.populate_obj(page)
            page.save()
            page.delete_cache()
            page_saved.send(page,
                            user=current_user,
                            message=form.message.data.encode('utf-8'))
            flash('"%s" was saved.' % page.title, 'success')
            return redirect(url_for('display', url=url))
    form.checksum.data = checksum
    extra_context = {}
    pre_edit.send(page, url=url, user=current_user, extra_context=extra_context)
    return render_template('editor.html', form=form, page=page, conflict=conflict,
                           markup=markup, **extra_context)


@app.route('/preview/', methods=['POST'])
@protect(True)
def preview():
    a = request.form
    data = {}
    data['html'], data['body'], data['meta'] = markup(a['body']).process()
    return data['html']


@app.route('/<path:url>/_move', methods=['GET', 'POST'])
@protect(True)
def move(url):
    page = wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        wiki.move(url, newurl)
        return redirect(url_for('.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@app.route('/<path:url>/_delete', methods=['POST'])
@protect(True)
def delete(url):
    page = wiki.get_or_404(url)
    wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title)
    return redirect(url_for('home'))


@app.route('/tags/')
@protect(False)
def tags():
    tags = wiki.get_tags()
    return render_template('tags.html', tags=tags)


@app.route('/tag/<string:name>/')
@protect(False)
def tag(name):
    tagged = wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@app.route('/search/', methods=['GET', 'POST'])
@protect(False)
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = wiki.search(form.term.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@app.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = app.users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('index'))
    return render_template('login.html', form=form)


@app.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('index'))


@app.route('/user/')
def user_index():
    pass


@app.route('/user/signup/', methods=['GET', 'POST'])
def user_signup():
    form = SignupForm()
    if form.validate_on_submit():
        active_user = app.config.get('PERMISSIONS', DEFAULT_PERMISSIONS) != PERMISSIONS_PRIVATE
        app.users.add_user(form.name.data, form.password.data,
                           form.full_name.data, form.email.data, active_user,
                           authentication_method=get_default_authentication_method())
        flash('You were registered successfully. Please login now.', 'success')
        if not active_user:
            flash('Your user is inactive by default, please contact the wiki admin', 'error')
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('signup.html', form=form)


@app.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@app.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


#===============================================================================
# LOAD EXTENSIONS
#===============================================================================

for ext in app.config.get('EXTENSIONS', []):
    mod = core.get_extension(ext)
    mod.init(app)


#===============================================================================
# MAIN
#===============================================================================

if __name__ == "__main__":
    print(__doc__)
