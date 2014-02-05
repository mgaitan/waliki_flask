#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)


#===============================================================================
# DOCS
#===============================================================================

"""Convert a waliki page to pdf

"""


#===============================================================================
# IMPORTS
#===============================================================================

import sys
import os.path
import subprocess
import tempfile

from flask import Blueprint, send_file, current_app, url_for


#===============================================================================
# BLUEPRINT
#===============================================================================

pdf = Blueprint('pdf', __name__,
                template_folder='templates')


#===============================================================================
# SLOTS
#===============================================================================

def extra_action(page, **extra):
    context = extra['extra_context']
    actions = context.get('extra_actions', [])
    actions.append(('Get as PDF', url_for('pdf.get_as_pdf', url=page.url)))
    context['extra_actions'] = actions


#===============================================================================
# INITIALIZATION
#===============================================================================

REQUIREMENTS = ["rst2pdf"]

def init(app):
    if app.config.get('MARKUP') == 'restructuredtext':
        app.register_blueprint(pdf)
        app.signals.signal('pre-display').connect(extra_action)


#===============================================================================
# ROUTES
#===============================================================================

@pdf.route('/<path:url>/_pdf')
def get_as_pdf(url):
    page = current_app.wiki.get_or_404(url)
    with tempfile.NamedTemporaryFile(suffix='.pdf') as output:
        outfile = output.name
    virtualenv_rst2pdf = os.path.join(os.path.dirname(sys.executable),
                                      'rst2pdf')
    if os.path.isfile(virtualenv_rst2pdf):
        rst2pdf = virtualenv_rst2pdf
    else:
        rst2pdf = 'rst2pdf'
    cmd = [rst2pdf, page.path, "-o", outfile]
    try:
        subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        return "Fail to generate output.\n\n{0}".format(e)
    filename = page.title.replace('/', '-').replace('..', '-')  # securitize
    return send_file(outfile, as_attachment=True,
                     attachment_filename="%s.pdf" % filename)


#===============================================================================
# MAIN
#===============================================================================

if __name__ == "__main__":
    print(__doc__)
