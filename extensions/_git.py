import os

from git import *
from gitdb import IStream
from StringIO import StringIO


class GitPlugin(object):

    def __init__(self, content_dir='content'):
        self.content_dir = content_dir
        if os.path.isdir(os.path.join(content_dir, '.git')):
            self.repository = Repo(content_dir, odbt=GitDB)
        else:
            if not os.path.isdir(content_dir):
                os.makedirs(content_dir)
            os.chdir(content_dir)
            self.repository = Repo.init()

    def _create_blob_for(self, path):
        repo = self.repository
        page_abspath = os.path.join(os.path.split(self.repository.working_dir)[0], path)
        data = open(page_abspath, 'r').read()
        istream = IStream('blob', len(data), StringIO(data))
        repo.odb.store(istream)
        blob_path = path.split(self.content_dir + os.path.sep)[1]   # remove "content/"
        blob = Blob(repo, istream.binsha, 0100644, blob_path)
        return blob

    def commit(self, page, message=u''):
        index = self.repository.index
        blob = self._create_blob_for(page.path)
        if os.path.isfile(blob.abspath):
            index.add([blob.path])
        else:
            index.add([IndexEntry.from_blob(blob)])
        return index.commit(message)


def git_plugin(page, **extra):
    gitp = GitPlugin()
    gitp.commit(page, extra['message'])