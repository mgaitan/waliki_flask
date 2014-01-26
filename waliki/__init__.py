# -*- coding: utf-8 -*-
import binascii
import hashlib
import mimetypes
import os
import re
import textwrap
import markdown
import docutils.core
import docutils.io
import json
from rst2html5 import HTML5Writer
from functools import wraps
from flask import (Flask, render_template, flash, redirect, url_for, request,
                   send_from_directory, abort)
from flask.ext.login import (LoginManager, login_required, current_user,
                             login_user, logout_user)
from flask.ext.script import Manager
from flask.ext.wtf import Form
from wtforms import (TextField, TextAreaField, PasswordField, HiddenField)
from wtforms.validators import (Required, ValidationError, Email)
from extensions.cache import cache
from signals import wiki_signals, page_saved, pre_display, pre_edit

from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter
from pygments import highlight
"""
    Markup classes
    ~~~~~~~~~~~~~~
"""
file_exts = {}

def get_markup(path):
    # build mapping of extensions to handlers, if necessary
    if not file_exts:
        for s in Markup.__subclasses__():
            if hasattr(s, 'EXTENSION'):
                file_exts.update(dict([(x, s) for x in s.EXTENSION]))

    # 1. filename match against each EXTENSION
    try:
        this_ext = "." + path.split('.')[-1]
        if this_ext in file_exts.keys():
            return file_exts[this_ext]
    except:
        # find by extension failed, press on
        pass

    # 2. handle images and other raw files
    (this_type, zipped) = mimetypes.guess_type(path, strict=False)
    if this_type:
        if this_type.startswith('image/') or zipped:
            return RawHandler

    # 3. pygments
    try:
        lexer = get_lexer_for_filename(path)
        if lexer:
            return HighlightedCodeFactory(lexer)
    except ValueError:
        pass

    # 4. all else failed, plaintext
    return Plaintext

class Markup(object):
    """ Base markup class."""
    NAME = 'Text'
    META_LINE = '%s: %s\n'
    EXTENSION = []
    HOWTO = """ """

    def __init__(self, raw_content):
        self.raw_content = raw_content

    @classmethod
    def render_meta(cls, key, value):
        return cls.META_LINE % (key, value)

    def process(self):
        """
        return (html, body, meta) where HTML is the rendered output
        body is the the editable content (text), and meta is
        a dictionary with at least ['title', 'tags'] keys
        """
        raise NotImplementedError("override in a subclass")

    @classmethod
    def howto(cls):
        return cls(textwrap.dedent(cls.HOWTO)).process()[0]


class Markdown(Markup):
    NAME = 'markdown'
    META_LINE = '%s: %s\n'
    EXTENSION = ['.md', '.mdwn']
    HOWTO = """
        This editor is [markdown][] featured.

            * I am
            * a
            * list

        Turns into:

        * I am
        * a
        * list

        `**bold** and *italics*` turn into **bold** and *italics*. Very easy!

        Create links with `[Wiki](http://github.com/alexex/wiki)`.
        They turn into [Wiki][http://github.com/alexex/wiki].

        Headers are as follows:

            # Level 1
            ## Level 2
            ### Level 3

        [markdown]: http://daringfireball.net/projects/markdown/
        """

    def process(self):
        # Processes Markdown text to HTML, returns original markdown text,
        # and adds meta
        md = markdown.Markdown(['codehilite', 'fenced_code', 'meta'])
        html = md.convert(self.raw_content)

        try:
            meta_lines, body = self.raw_content.split('\n\n', 1)
        except ValueError:
            body = self.raw_content

        if hasattr(md, 'Meta') and md.Meta:
            meta = md.Meta
        else:
            meta = {}
        return html, body, meta


class RestructuredText(Markup):
    NAME = 'restructuredtext'
    META_LINE = '.. %s: %s\n'
    IMAGE_LINE = '.. image:: %(url)s'
    LINK_LINE = '`%(filename)s <%(url)s>`_'

    EXTENSION = ['.rst']
    HOWTO = """
        This editor is `reStructuredText`_ featured::

            * I am
            * a
            * list

        Turns into:

        *  I am
        *  a
        *  list

        ``**bold** and *italics*`` turn into **bold** and *italics*. Very easy!

        Create links with ```Wiki <http://github.com/alexex/wiki>`_``.
        They turn into `Wiki <https://github.com/alexex/wiki>`_.

        Headers are just any underline (and, optionally, overline).
        For example::

            Level 1
            *******

            Level 2
            -------

            Level 3
            +++++++

        .. _reStructuredText: http://docutils.sourceforge.net/rst.html
        """

    def process(self):
        settings = {'initial_header_level': 2,
                    'record_dependencies': True,
                    'stylesheet_path': None,
                    'link_stylesheet': True,
                    'syntax_highlight': 'short',
                    }

        html = self._rst2html(self.raw_content,
                                    settings_overrides=settings)

        # Convert unknow links to internal wiki links.
        # Examples:
        #   Something_ will link to '/something'
        #  `something great`_  to '/something_great'
        #  `another thing <thing>`_  '/thing'
        refs = re.findall(r'Unknown target name: "(.*)"', html)
        if refs:
            content = self.raw_content + self.get_autolinks(refs)
            html = self._rst2html(content, settings_overrides=settings)
        meta_lines, body = self.raw_content.split('\n\n', 1)
        meta = self._parse_meta(meta_lines.split('\n'))
        return html, body, meta

    def get_autolinks(self, refs):
        autolinks = '\n'.join(['.. _%s: /%s' % (ref, urlify(ref, False))
                               for ref in refs])
        return '\n\n' + autolinks

    def _rst2html(self, source, source_path=None,
                  source_class=docutils.io.StringInput,
                  destination_path=None, reader=None, reader_name='standalone',
                  parser=None, parser_name='restructuredtext', writer=None,
                  writer_name=None, settings=None, settings_spec=None,
                  settings_overrides=None, config_section=None,
                  enable_exit_status=None):

        if not writer:
            writer = HTML5Writer()

        # Taken from Nikola
        # http://bit.ly/14CmQyh
        output, pub = docutils.core.publish_programmatically(
            source=source, source_path=source_path, source_class=source_class,
            destination_class=docutils.io.StringOutput,
            destination=None, destination_path=destination_path,
            reader=reader, reader_name=reader_name,
            parser=parser, parser_name=parser_name,
            writer=writer, writer_name=writer_name,
            settings=settings, settings_spec=settings_spec,
            settings_overrides=settings_overrides,
            config_section=config_section,
            enable_exit_status=enable_exit_status)
        return pub.writer.parts['body']

    def _parse_meta(self, lines):
        """ Parse Meta-Data. Taken from Python-Markdown"""
        META_RE = re.compile(r'^\.\.\s(?P<key>.*?): (?P<value>.*)')
        meta = {}
        key = None
        for line in lines:
            if line.strip() == '':
                continue
            m1 = META_RE.match(line)
            if m1:
                key = m1.group('key').lower().strip()
                value = m1.group('value').strip()
                try:
                    meta[key].append(value)
                except KeyError:
                    meta[key] = [value]
        return meta

def HighlightedCodeFactory(new_lexer):
    class HighlightedCode(Markup):
        NAME = 'highlight'
        META_LINE = ''
        EXTENSION = []
        HOWTO = """
            This editor is syntax-highlighted sourcecode.

            Tags are not supported.
            """
        lexer = new_lexer

        @classmethod
        def render_meta(cls, key, value):
            return None

        def process(self):
            formatter = HtmlFormatter(style='default')
            html = '<style>' + formatter.get_style_defs() + '</style>' + highlight(self.raw_content, self.lexer, formatter)
            body = self.raw_content
            meta = {'tags': 'source code'}
            return html, body, meta

    return HighlightedCode

class RawHandler(Markup):
    NAME = 'raw'
    META_LINE = ''
    EXTENSION = []
    HOWTO = """
        Raw data (unrendered).
        """
    @classmethod
    def render_meta(cls, key, value):
        return None

    def process(self):
        meta = {'tags': 'raw data'}
        return ("", "", meta)

class Plaintext(Markup):
    NAME = 'plaintext'
    META_LINE = ''
    EXTENSION = ['.txt']
    HOWTO = """
        This editor is plaintext.
        """
    @classmethod
    def render_meta(cls, key, value):
        return None

    def process(self):
        html = '<pre>' + self.raw_content + '</pre>'
        body = '<pre>' + self.raw_content + '</pre>'
        meta = {}
        return html, body, meta

"""
    Wiki classes
    ~~~~~~~~~~~~
"""


class Page(object):
    def __init__(self, path, url, new=False):
        self.path = path
        self.url = url
        self.markup = get_markup(path)
        self._raw = self.markup.NAME == 'raw'
        self._meta = {}
        self.directory = False
        if (os.path.exists(self.path) and
            os.path.isdir(self.path)):
            self.directory = True

        if not new and not self.directory:
            self.load()
            self.render()

    def load(self, content=None):
        if not content and not self._raw:
            with open(self.path, 'rU') as f:
                content = f.read().decode('utf-8')
        self.content = self.markup(content)

    def render(self):
        self._html, self.body, self._meta = self.content.process()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.path)

    def save(self, update=True):
        folder = os.path.dirname(self.path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(self.path, 'w') as f:
            if self.markup.META_LINE:
                for key in sorted(self._meta.keys()):
                    value = self._meta[key]
                    line = self.markup.META_LINE % (key, value)
                    f.write(line.encode('utf-8'))
                f.write('\n'.encode('utf-8'))
            f.write(self.body.replace('\r\n', os.linesep).encode('utf-8'))
        if update:
            self.load()
            self.render()

    @property
    def meta(self):
        return self._meta

    def __getitem__(self, name):
        item = self._meta[name]
        if len(item) == 1:
            return item[0]
        return item

    def __setitem__(self, name, value):
        self._meta[name] = value

    @property
    def html(self):
        return self._html

    @cache.memoize()
    def __html__(self):
        return self.html

    def delete_cache(self):
        cache.delete(self.__html__.make_cache_key(self.__html__.uncached,
                                                  self))

    @property
    def title(self):
        if 'title' not in self._meta:
            return os.path.basename(self.path)
        return self['title']

    @title.setter               # NOQA
    def title(self, value):
        self['title'] = value

    @property
    def tags(self):
        if 'tags' not in self._meta:
            return ''
        return self['tags']

    @tags.setter               # NOQA
    def tags(self, value):
        self['tags'] = value

    # Hide title and tags fields for files where they shouldn't be written
    @property
    def nometa(self):
        return not bool(self.markup.META_LINE)

    @nometa.setter
    def nometa(self, value):
        pass

    @property
    def crumbs(self):
        urls = []
        parts = self.url.split('/')
        for x in range(len(parts)):
            urls.append((parts[x], '/' + '/'.join(parts[0:x+1])))
        return urls

class Wiki(object):
    def __init__(self, root):
        self.root = root

    def path(self, url):
        return os.path.join(self.root, url)

    def exists(self, url):
        path = self.path(url)
        return os.path.exists(path)

    def get(self, url):
        path = os.path.join(self.root, url)
        if self.exists(url):
            return Page(path, url)
        return None

    def get_or_404(self, url):
        page = self.get(url)
        if page:
            return page
        abort(404)

    def get_bare(self, url):
        path = self.path(url)
        if self.exists(url):
            return False
        return Page(path, url, new=True)

    def move(self, url, newurl):
        newdir = os.path.join(self.root, os.path.dirname(newurl))
        if not os.path.exists(newdir):
            os.makedirs(newdir)
        os.rename(
            os.path.join(self.root, url),
            os.path.join(self.root, newurl)
        )

    def delete(self, url):
        path = self.path(url)
        if not self.exists(url):
            return False
        os.remove(path)
        return True

    def index(self, attr=None, prefix=None):
        def _walk(directory, path_prefix=()):
            for name in os.listdir(directory):
                if name in ['.git', 'cache', 'templates']: continue
                fullname = os.path.join(directory, name)
                if os.path.isdir(fullname):
                    _walk(fullname, path_prefix + (name,))
                else:
                    if not path_prefix:
                        url = name
                    else:
                        url = os.path.join('/'.join(path_prefix), name)
                    if attr:
                        pages[getattr(page, attr)] = page
                    else:
                        pages.append(Page(fullname, url.replace('\\', '/')))

        if attr:
            pages = {}
        else:
            pages = []
        if prefix:
            _walk(os.path.join(self.root, prefix), path_prefix = tuple(prefix.split('/')))
        else:
            _walk(self.root)
        if not attr:
            field = app.config.get('SORT')
            return sorted(pages, key=lambda x: getattr(x, field).lower())
        return pages

    def get_by_title(self, title):
        pages = self.index(attr='title')
        return pages.get(title)

    def get_tags(self):
        pages = self.index()
        tags = {}
        for page in pages:
            pagetags = page.tags.split(',')
            for tag in pagetags:
                tag = tag.strip()
                if tag == '':
                    continue
                elif tags.get(tag):
                    tags[tag].append(page)
                else:
                    tags[tag] = [page]
        return tags

    def index_by_tag(self, tag):
        pages = self.index()
        tagged = []
        for page in pages:
            if tag in page.tags:
                tagged.append(page)
        return sorted(tagged, key=lambda x: x.title.lower())

    def search(self, term, attrs=['title', 'tags', 'body']):
        pages = self.index()
        regex = re.compile(term)
        matched = []
        for page in pages:
            for attr in attrs:
                if regex.search(getattr(page, attr)):
                    matched.append(page)
                    break
        return matched


"""
    User classes & helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""


class UserManager(object):
    """A very simple user Manager, that saves it's data as json."""
    def __init__(self, path):
        self.file = os.path.join(path, 'users.json')

    def read(self):
        if not os.path.exists(self.file):
            return {}
        with open(self.file) as f:
            data = json.loads(f.read())
        return data

    def write(self, data):
        with open(self.file, 'w') as f:
            f.write(json.dumps(data, indent=2))

    def add_user(self, name, password, full_name, email,
                 active=True, roles=[], authentication_method=None):
        users = self.read()
        if users.get(name):
            return False
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        new_user = {
            'active': active,
            'roles': roles,
            'authentication_method': authentication_method,
            'authenticated': False,
            'full_name': full_name,
            'email': email
        }
        # Currently we have only two authentication_methods: cleartext and
        # hash. If we get more authentication_methods, we will need to go to a
        # strategy object pattern that operates on User.data.
        if authentication_method == 'hash':
            new_user['hash'] = make_salted_hash(password)
        elif authentication_method == 'cleartext':
            new_user['password'] = password
        else:
            raise NotImplementedError(authentication_method)
        users[name] = new_user
        self.write(users)
        userdata = users.get(name)
        return User(self, name, userdata)

    def get_user(self, name):
        users = self.read()
        userdata = users.get(name)
        if not userdata:
            return None
        return User(self, name, userdata)

    def delete_user(self, name):
        users = self.read()
        if not users.pop(name, False):
            return False
        self.write(users)
        return True

    def update(self, name, userdata):
        data = self.read()
        data[name] = userdata
        self.write(data)


class User(object):
    def __init__(self, manager, name, data):
        self.manager = manager
        self.name = name
        self.data = data

    def get(self, option):
        return self.data.get(option)

    def set(self, option, value):
        self.data[option] = value
        self.save()

    def save(self):
        self.manager.update(self.name, self.data)

    def is_authenticated(self):
        return self.data.get('authenticated')

    def is_active(self):
        return self.data.get('active')

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.name

    def check_password(self, password):
        """Return True, return False, or raise NotImplementedError if the
        authentication_method is missing or unknown."""
        authentication_method = self.data.get('authentication_method', None)
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        # See comment in UserManager.add_user about authentication_method.
        if authentication_method == 'hash':
            result = check_hashed_password(password, self.get('hash'))
        elif authentication_method == 'cleartext':
            result = (self.get('password') == password)
        else:
            raise NotImplementedError(authentication_method)
        return result


def get_default_authentication_method():
    return app.config.get('DEFAULT_AUTHENTICATION_METHOD', 'hash')


def make_salted_hash(password, salt=None):
    if not salt:
        salt = os.urandom(64)
    d = hashlib.sha512()
    d.update(salt[:32])
    d.update(password)
    d.update(salt[32:])
    return binascii.hexlify(salt) + d.hexdigest()


def check_hashed_password(password, salted_hash):
    salt = binascii.unhexlify(salted_hash[:128])
    return make_salted_hash(password, salt) == salted_hash


def protect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if app.config.get('PRIVATE') and not current_user.is_authenticated():
            return loginmanager.unauthorized()
        return f(*args, **kwargs)
    return wrapper


"""
    Forms
    ~~~~~
"""


def urlify(url, protect_specials_url=True):
    # Cleans the url and corrects various errors.
    # Remove multiple spaces and leading and trailing spaces
    if (protect_specials_url and
            re.match(r'^(?i)(user|tag|create|search|index)', url)):
        url = '-' + url
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
    nometa = HiddenField('')
    message = TextField('')


class LoginForm(Form):
    name = TextField('Username', [Required()])
    password = PasswordField('Password', [Required()])

    def validate_name(form, field):
        user = users.get_user(field.data)
        if not user:
            raise ValidationError('This username does not exist.')

    def validate_password(form, field):
        user = users.get_user(form.name.data)
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
        user = users.get_user(field.data)
        if user:
            raise ValidationError('This username is already taken')

    def validate_password(form, field):
        if len(field.data) < 4:
            raise ValidationError('The password is too short')


"""
    Application Setup
    ~~~~~~~~~
"""

app = Flask(__name__)
app.debug = True
app.config['CONTENT_DIR'] = os.path.abspath('content')
app.config['TITLE'] = 'wiki'
app.config['MARKUP'] = 'markdown'  # default markup for editing new pages
app.config['SORT'] = 'title'
app.config['THEME'] = 'elegant'  # more at waliki/static/codemirror/theme
try:
    app.config.from_pyfile(
        os.path.join(app.config.get('CONTENT_DIR'), 'config.py')
    )
except IOError:
    print ("Startup Failure: You need to place a "
           "config.py in your content directory.")

CACHE_DIR = os.path.join(app.config.get('CONTENT_DIR'), 'cache')
cache.init_app(app, config={'CACHE_TYPE': 'filesystem',
                            'CACHE_DIR': CACHE_DIR})
manager = Manager(app)

loginmanager = LoginManager()
loginmanager.init_app(app)
loginmanager.login_view = 'user_login'
markup = dict([(klass.NAME, klass) for klass in
               Markup.__subclasses__()])[app.config.get('MARKUP')]

wiki = Wiki(app.config.get('CONTENT_DIR'))

# FIX ME: This monkeypatching is pollution crap .
#         Should be possible to import them wherever,
#         Wiki class should be a singleton.
app.wiki = wiki
app.signals = wiki_signals
app.EditorForm = EditorForm


users = UserManager(app.config.get('CONTENT_DIR'))


@loginmanager.user_loader
def load_user(name):
    return users.get_user(name)


"""
    Routes
    ~~~~~~
"""


@app.route('/')
@protect
def home():
    page = wiki.get_tags()['HOMEPAGE'][0]
    if page:
        return display(page.url)
    return render_template('home.html')


@app.route('/index/')
@protect
def index():
    pages = wiki.index()
    return render_template('index.html', pages=pages)


@app.route('/<path:url>/')
@app.route('/<path:url>')
@protect
def display(url):
    page = wiki.get(url)
    if not page:
        flash('The page "{0}" does not exist, '
              'feel free to make it now!'.format((url)), 'warning')
        return redirect(url_for('edit', url=urlify(url)))

    if page._raw:
        directory = os.path.dirname(page.path)
        filename = os.path.basename(page.path)
        return send_from_directory(directory, filename)

    extra_context = {}
    pre_display.send(page, user=current_user, extra_context=extra_context)
    if page.directory:
        pages = wiki.index(prefix=page.url)
        return render_template('directory.html', pages=pages, crumbs=page.crumbs, **extra_context)
    else:
        return render_template('page.html', page=page, **extra_context)


@app.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for('edit', url=urlify(form.url.data)))
    return render_template('create.html', form=form)


@app.route('/<path:url>/_edit', methods=['GET', 'POST'])
@protect
def edit(url):
    page = wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
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
    extra_context = {}
    pre_edit.send(page, url=url, user=current_user, extra_context=extra_context)
    if hasattr(page, 'markup'):
        my_markup = page.markup
    else:
        my_markup = markup

    return render_template('editor.html', form=form, page=page,
                           markup=my_markup, **extra_context)


@app.route('/preview/', methods=['POST'])
@protect
def preview():
    a = request.form
    data = {}
    try:
        my_markup = wiki.get(a['url']).markup
    except:
        my_markup = markup
    data['html'], data['body'], data['meta'] = my_markup(a['body']).process()
    return data['html']


@app.route('/<path:url>/_move', methods=['GET', 'POST'])
@protect
def move(url):
    page = wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        wiki.move(url, newurl)
        return redirect(url_for('.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@app.route('/<path:url>/_delete', methods=['POST'])
@protect
def delete(url):
    page = wiki.get_or_404(url)
    wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title)
    return redirect(url_for('home'))


@app.route('/tags/')
@protect
def tags():
    tags = wiki.get_tags()
    return render_template('tags.html', tags=tags)


@app.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@app.route('/search/', methods=['GET', 'POST'])
@protect
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
        user = users.get_user(form.name.data)
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
        users.add_user(form.name.data, form.password.data,
                       form.full_name.data, form.email.data)
        flash('You were registered successfully. Please login now.', 'success')
        return redirect(request.args.get("next") or url_for('index'))
    return render_template('signup.html', form=form)


@app.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@app.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


# Load extensions
for ext in app.config.get('EXTENSIONS', []):
    mod = __import__('extensions.%s' % ext, fromlist=['init'])
    mod.init(app)

if __name__ == '__main__':
    manager.run()
