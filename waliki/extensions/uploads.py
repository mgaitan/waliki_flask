#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)


#===============================================================================
# DOCS
#===============================================================================

"""Plugin for upload files to waliki webpages"""


#===============================================================================
# IMPORTS
#===============================================================================

import os.path
import imghdr

from flaskext.uploads import (
    UploadSet, ALL, configure_uploads, patch_request_class
)
from flask import (render_template, flash, request, Blueprint, current_app,
                   abort, send_file, url_for, jsonify)


#===============================================================================
# CONSTANTS
#===============================================================================

CLOSE_WINDOW_HTML = """
<html>
<head>
<script type="text/javascript">
    window.close();
</script>
</head>
<body>
</body>
</html>"""


#===============================================================================
# BLUEPRINT AND BASE SETUP
#===============================================================================

def default_dest(app):
    return os.path.join(app.config.get('CONTENT_DIR'), 'uploads')

media = UploadSet('media', ALL, default_dest=default_dest)

uploads = Blueprint('uploads',  __name__, template_folder='templates')


#===============================================================================
# SLOT
#===============================================================================

def extra_actions(page, **extra):
    context = extra['extra_context']
    actions = context.get('extra_actions', [])
    actions.append(('Attachments', url_for('uploads.upload', url=extra.get('url'))))
    context['extra_actions'] = actions


#===============================================================================
# INITIALIZER
#===============================================================================

REQUIREMENTS = ["Flask-Uploads"]

def init(app):
    app.register_blueprint(uploads)
    configure_uploads(app, media)
    app.signals.signal('pre-edit').connect(extra_actions)
    patch_request_class(app, 32 * 1024 * 1024)      # limit 32mb


#===============================================================================
# ROUTES
#===============================================================================

@uploads.route('/<path:url>/_upload', methods=['GET', 'POST'])
def upload(url):
    last_attached = None
    page = current_app.wiki.get_or_404(url)
    if request.method == 'POST' and 'attach' in request.files:
        last_attached = request.files['attach']
        media.save(last_attached, folder=page.url)
        flash('"%s" was attached succesfully to /%s' % (last_attached.filename,
                                                        page.url))
    try:
        files = os.listdir(os.path.join(current_app.config.get('CONTENT_DIR'),
                                    'uploads', page.url))
    except OSError:
        files = []
    return render_template('upload.html', page=page, files=files,
                            markup=current_app.wiki.markup)


def _base_file(url, filename):
    page = current_app.wiki.get_or_404(url)
    directory = os.path.join(current_app.config.get('CONTENT_DIR'),
                                    'uploads', url)
    try:
        files = os.listdir(directory)
    except OSError:
        files = []
    if not filename in files:
        abort(404)
    outfile = os.path.join(directory, filename)
    return outfile


@uploads.route('/<path:url>/_attachment/<filename>')
def get_file(url, filename):
    outfile = _base_file(url, filename)
    # by default only images are embeddable.
    as_attachment = ((not imghdr.what(outfile) and 'embed' not in request.args)
                     or 'as_attachment' in request.args)
    return send_file(outfile, as_attachment=as_attachment)


@uploads.route('/<path:url>/_remove/<filename>', methods=['POST', 'DELETE'])
def remove_file(url, filename):
    outfile = _base_file(url, filename)
    try:
        os.remove(outfile)
    finally:
        return jsonify({'removed': filename})
    return jsonify({'removed': None})


#===============================================================================
# MAIN
#===============================================================================

if __name__ == "__main__":
    print(__doc__)
