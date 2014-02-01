#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014, Martín Gaitán
# Copyright (c) 2012-2013, Alexander Jung-Loddenkemper
# This file is part of Waliki (http://waliki.nqnwebs.com/)
# License: BSD (https://github.com/mgaitan/waliki/blob/master/LICENSE)


#===============================================================================
# DOCS
#===============================================================================

"""All supported markups

"""

#===============================================================================
# IMPORTS
#===============================================================================

import re
import docutils.core
import docutils.io

import markdown
import textwrap
from rst2html5 import HTML5Writer

import wiki


#===============================================================================
# MARKUP BASE
#===============================================================================

class Markup(object):
    """ Base markup class."""
    NAME = 'Text'
    META_LINE = '%s: %s\n'
    EXTENSION = '.txt'
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


#===============================================================================
# MARKDOWN
#===============================================================================

class Markdown(Markup):
    NAME = 'markdown'
    META_LINE = '%s: %s\n'
    EXTENSION = '.md'
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
        meta_lines, body = self.raw_content.split('\n\n', 1)
        meta = md.Meta
        return html, body, meta


#===============================================================================
# RESTRUCTURED TEXT
#===============================================================================

class RestructuredText(Markup):
    NAME = 'restructuredtext'
    META_LINE = '.. %s: %s\n'
    IMAGE_LINE = '.. image:: %(url)s'
    LINK_LINE = '`%(filename)s <%(url)s>`_'

    EXTENSION = '.rst'
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
        autolinks = '\n'.join(['.. _%s: /%s' % (ref, wiki.urlify(ref, False))
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


#===============================================================================
# MAIN
#===============================================================================

if __name__ == "__main__":
    print(__doc__)
