import os
import re
from flask import (Blueprint, render_template, current_app,
                   request, url_for, redirect, abort)
from git import *
from gitdb import IStream
from StringIO import StringIO
import json


gitplugin = Blueprint('gitplugin', __name__, template_folder='templates')


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
            os.environ['GIT_AUTHOR_NAME'] = user.data.get('full_name', user.name).encode('utf-8')
            os.environ['GIT_AUTHOR_EMAIL'] = user.data.get('email', '').encode('utf-8')
        return index.commit(message)

    def last_rev(self, page):
        path = self._get_blob_path(page.path)
        log = self.repository.git.log('--format=%an %ad', '--date=relative',
                                      path).split('\n')[0]
        page.footer = u'Last edited by %s' % log.decode('utf-8')

    def page_history(self, page):
        path = self._get_blob_path(page.path)
        data = [("commit", "%h"),
                ("author", "%an"),
                ("date", "%ad"),
                ("date_relative", "%ar"),
                ("message", "%s")]
        format = "{%s}" % ','.join([""" \"%s\": \"%s\" """ % item for item in data])
        output = self.repository.git.log('--format=%s' % format,
                                         '-z',
                                         '--shortstat', path)
        output = output.replace('\x00', '').split('\n')
        history = []
        for line in output:
            if line.startswith('{'):
                history.append(json.loads(line))
            else:
                insertion = re.match(r'.* (\d+) insertion', line)
                deletion = re.match(r'.* (\d+) deletion', line)
                history[-1]['insertion'] = int(insertion.group(1)) if insertion else 0
                history[-1]['deletion'] = int(deletion.group(1)) if deletion else 0
        return history

    def page_version(self, page, version):
        path = self._get_blob_path(page.path)
        try:
            return self.repository.git.show('%s:%s' % (version, path))
        except GitCommandError:
            return ''

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
        page.new = self.page_version(page, new)
        page.old = self.page_version(page, old)

"""
    Receivers
    ~~~~~~~~~
"""


def git_commit(page, **extra):
    current_app.git.commit(page, extra['user'], extra['message'])


def git_rev(page, **extra):
    current_app.git.last_rev(page)


def extra_actions(page, **extra):
    context = extra['extra_context']
    actions = context.get('extra_actions', [])
    actions.append(('History', url_for('gitplugin.history', url=page.url)))
    context['extra_actions'] = actions

"""
    Views
    ~~~~~
"""



@gitplugin.route('/<path:url>/_version/<version>')
def version(url, version):
    page = current_app.wiki.get_or_404(url)
    content = current_app.git.page_version(page, version)
    if not content:
        abort(404)
    page.delete_cache()
    page.load(content.decode('utf-8'))
    page.render()
    form = current_app.EditorForm(obj=page)
    form.message.data = 'Restored version @%s' % version
    return render_template('page_version.html', page=page,
                           version=version, form=form)


@gitplugin.route('/<path:url>/_diff/<new>..<old>', methods=['GET', 'POST'])
def diff(url, new, old):
    page = current_app.wiki.get_or_404(url)
    current_app.git.page_diff(page, old, new)
    return render_template('diff.html', page=page,
                           new_commit=new,
                           old_commit=old)


@gitplugin.route('/<path:url>/_history', methods=['GET', 'POST'])
def history(url):
    page = current_app.wiki.get_or_404(url)
    if request.method == 'POST':
        new, old = request.form.getlist('commit')
        return redirect(url_for('gitplugin.diff',
                                url=page.url, new=new, old=old))
    history = current_app.git.page_history(page)
    max_changes = max([(v['insertion'] + v['deletion']) for v in history])
    return render_template('history.html', page=page, history=history,
                           max_changes=max_changes)


"""
    Initializer
    ~~~~~~~~~~~
"""


def init(app):
    app.register_blueprint(gitplugin)
    app.signals.signal('page-saved').connect(git_commit)
    app.signals.signal('pre-display').connect(git_rev)
    app.signals.signal('pre-display').connect(extra_actions)
    app.git = GitManager(app.config['CONTENT_DIR'])
