import os.path
from flaskext.uploads import UploadSet, ALL, configure_uploads
from flask import redirect, render_template, flash, request, Blueprint


def default_dest(app):
    return os.path.join(app.config.get('CONTENT_DIR'), 'uploads')

media = UploadSet('media', ALL, default_dest=default_dest)

uploads = Blueprint('uploads',  __name__, template_folder='templates')

def init(app):
    app.register_blueprint(uploads)
    configure_uploads(app, media)


@uploads.route('/<path:url>/_upload', methods=['GET', 'POST'])
def upload(url):
    if request.method == 'POST' and 'photo' in request.files:
        media.save(request.files['photo'], folder=url)
        flash("Photo saved.")
    return render_template('upload.html')