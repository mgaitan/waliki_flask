import os
from flask import Blueprint, render_template, url_for, current_app
from git import *
from gitdb import IStream
from StringIO import StringIO
import json


gitplugin = Blueprint('gitplugin', __name__,
                       template_folder='templates')


"""
    Helpers
    ~~~~~~~
"""

class GitManager(object):
    def __init__(self, content_dir):
        self.content_dir = content_dir
        if os.path.isdir(os.path.join(content_dir, '.git')):
            self.repository = Repo(content_dir, odbt=GitDB)
        else:
            if not os.path.isdir(content_dir):
                os.makedirs(content_dir)
            os.chdir(content_dir)
            self.repository = Repo.init()

    def _get_blob_path(self, path):
        # remove "content/"
        return path.split(self.content_dir + os.path.sep)[1]

    def _create_blob_for(self, path):
        repo = self.repository
        page_abspath = os.path.join(os.path.split(self.repository.working_dir)[0], path)
        data = open(page_abspath, 'r').read()
        istream = IStream('blob', len(data), StringIO(data))
        repo.odb.store(istream)
        blob_path = self._get_blob_path(path)
        blob = Blob(repo, istream.binsha, 0100644, blob_path)
        return blob

    def commit(self, page, user=None, message=u''):
        index = self.repository.index
        blob = self._create_blob_for(page.path)
        if os.path.isfile(blob.abspath):
            index.add([blob.path])
        else:
            index.add([IndexEntry.from_blob(blob)])
        if user and user.is_authenticated():
            os.environ['GIT_AUTHOR_NAME'] = user.data.get('full_name', user.name)
            os.environ['GIT_AUTHOR_EMAIL'] = user.data.get('email', '')
        return index.commit(message)

    def last_rev(self, page):
        path = self._get_blob_path(page.path)
        log = self.repository.git.log('--format=%an %ad', '--date=relative',
                                      path).split('\n')[0]
        page.footer = 'Last edition by %s' % log


    def page_history(self, page):
        path = self._get_blob_path(page.path)
        format = """{\"commit\": \"%h\", \"author\": \"%an\", \"date\": \"%ad\", \"message\": \"%s\"}"""
        history = self.repository.git.log('--format=%s' % format, path).split('\n')
        return [json.loads(log) for log in history]

    def page_diff(self, page, old=None, new=None):
        path = self._get_blob_path(page.path)
        history = self.repository.git.log('--format=%h', path).split('\n')
        if old is None:
            try:
                old = history[1]
            except IndexError:
                pass
        if new is None:
            new = history[0]
        page.old_content = self.repository.git.show('%s:%s' % (old, path)) if old else ''
        page.new_content = self.repository.git.show('%s:%s' % (new, path))

"""
    Receivers
    ~~~~~~~~~
"""


def git_commit(page, **extra):
    current_app.git.commit(page, extra['user'], extra['message'])


def git_rev(page, **extra):
    current_app.git.last_rev(page)


"""
    Initializer
    ~~~~~~~~~~~
"""


def init_git(app):
    app.register_blueprint(gitplugin)
    app.signals.signal('page-saved').connect(git_commit)
    app.signals.signal('pre-display').connect(git_rev)
    app.git = GitManager(app.config['CONTENT_DIR'])


"""
    Views
    ~~~~~
"""


@gitplugin.route('/diff/<path:url>/', methods=['GET', 'POST'])
def diff(url):
    page = current_app.wiki.get_or_404(url)
    current_app.git.page_diff(page)
    return render_template('history.html', page=page)

@gitplugin.route('/history/<path:url>/', methods=['GET', 'POST'])
def history(url):
    page = current_app.wiki.get_or_404(url)
    history = current_app.git.page_history(page)
    return render_template('history.html', page=page, history=history)




