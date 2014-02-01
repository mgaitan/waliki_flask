#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask.signals import Namespace

wiki_signals = Namespace()

page_saved = wiki_signals.signal('page-saved')
pre_edit = wiki_signals.signal('pre-edit')
pre_display = wiki_signals.signal('pre-display')
