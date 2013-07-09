import os.path
from flaskext.uploads import UploadSet, ALL, configure_uploads
from flask import (render_template, flash, request, Blueprint, current_app,
                   abort, send_file, url_for)


def default_dest(app):
    return os.path.join(app.config.get('CONTENT_DIR'), 'uploads')

media = UploadSet('media', ALL, default_dest=default_dest)

uploads = Blueprint('uploads',  __name__, template_folder='templates')


def extra_actions(page, **extra):
    import ipdb; ipdb.set_trace()
    context = extra['extra_context']
    actions = context.get('extra_actions', [])
    actions.append(('Attachments', url_for('uploads.upload', url=page.url)))
    context['extra_actions'] = actions


def init(app):
    app.register_blueprint(uploads)
    configure_uploads(app, media)
    app.signals.signal('pre-edit').connect(extra_actions)




@uploads.route('/<path:url>/_upload', methods=['GET', 'POST'])
def upload(url):
    page = current_app.wiki.get_or_404(url)
    if request.method == 'POST' and 'attach' in request.files:
        media.save(request.files['attach'], folder=page.url)
        flash("File uploaded")
    try:
        files = os.listdir(os.path.join(current_app.config.get('CONTENT_DIR'),
                                    'uploads', page.url))
    except OSError:
        files = []
    return render_template('upload.html', page=page, files=files)


@uploads.route('/<path:url>/_attach/<filename>')
def get_file(url, filename):
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
    return send_file(outfile, as_attachment=False)
