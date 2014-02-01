#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)

from flask.signals import Namespace

wiki_signals = Namespace()

page_saved = wiki_signals.signal('page-saved')
pre_edit = wiki_signals.signal('pre-edit')
pre_display = wiki_signals.signal('pre-display')
