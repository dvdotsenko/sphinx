# -*- coding: utf-8 -*-
"""
    sphinx.writers.text
    ~~~~~~~~~~~~~~~~~~~

    Custom docutils writer for plain text.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
import re
import textwrap
from itertools import groupby

from six import iteritems, text_type, string_types
from six.moves import zip_longest

from docutils import nodes, writers
from docutils.utils import column_width

from sphinx import addnodes
from sphinx.locale import admonitionlabels, _

LAST = -1
NO_INDENT = -1
STDINDENT = 0


class NotSet:
    pass


class MarkdownTranslator(nodes.NodeVisitor):

    sectionchars = '*=-~"+`'

    def __init__(self, document, builder):
        nodes.NodeVisitor.__init__(self, document)
        self.builder = builder

        newlines = builder.config.text_newlines
        if newlines == 'windows':
            self.nl = '\r\n'
        elif newlines == 'native':
            self.nl = os.linesep
        else:
            self.nl = '\n'
        self.sectionchars = builder.config.text_sectionchars
        self.states = [[]]
        self.stateindent = [0]
        self.list_counter = []
        self.sectionlevel = 1
        self.lineblocklevel = 0
        self.table = None

    def add_text(self, text):
        self.states[LAST].append((NO_INDENT, text))

    def new_state(self, indent=STDINDENT):
        self.states.append([])
        self.stateindent.append(indent)

    def end_state(self, wrap=True, end=NotSet, first=None):

        if end is NotSet:
            end = ['']

        content = self.states.pop()
        maxindent = sum(self.stateindent)
        indent = self.stateindent.pop()
        result = []
        toformat = []

        def do_format():
            if not toformat:
                return
            res = ''.join(toformat).splitlines()
            if end:
                res += end
            result.append((indent, res))

        for itemindent, item in content:
            if itemindent == NO_INDENT:
                toformat.append(item)
            else:
                do_format()
                result.append((indent + itemindent, item))
                toformat = []

        do_format()
        if first is not None and result:
            itemindent, item = result[0]
            result_rest, result = result[1:], []
            if item:
                toformat = [first + ' '.join(item)]
                do_format()  # re-create `result` from `toformat`
                _dummy, new_item = result[0]
                result.insert(0, (itemindent - indent, [new_item[0]]))
                result[1] = (itemindent, new_item[1:])
                result.extend(result_rest)

        self.states[LAST].extend(result)

    def visit_document(self, node):
        self.new_state(0)

    def depart_document(self, node):
        self.end_state()
        self.body = self.nl.join(
            line and (' ' * indent + line)
            for indent, lines in self.states[0]
            for line in lines
        )

    def visit_start_of_file(self, node):
        # only occurs in the single-file builder
        # self.add_text('<span id="document-%s"></span>' % node['docname'])
        pass

    def depart_start_of_file(self, node):
        pass

    def visit_section(self, node):
        self._title_prefix = (u'#' * self.sectionlevel) + ' '
        self.sectionlevel += 1

    def depart_section(self, node):
        self.sectionlevel -= 1

    def visit_title(self, node):
        if isinstance(node.parent, nodes.Admonition):
            self.add_text(node.astext()+': ')
            raise nodes.SkipNode
        self.new_state(0)

    def depart_title(self, node):
        if isinstance(node.parent, nodes.section):
            title_prefix = self._title_prefix
        else:
            title_prefix = ''
        title = ''.join(
            payload
            for indent, payload in self.states.pop()
            if indent == NO_INDENT
        )
        self.stateindent.pop()
        self.states[LAST].append(
            (
                0,
                [
                    '',
                    '{} {}'.format(title_prefix, title),
                    ''
                ]
            )
        )

    def visit_Text(self, node):
        self.add_text(node.astext())

    def depart_Text(self, node):
        pass

    def unknown_visit(self, node):
        self.builder.info(u'== ({}) skipping: {}'.format(
            self.sectionlevel,
            node.__class__.__name__
        ))
        raise nodes.SkipNode
        # raise NotImplementedError('Unknown node: ' + node.__class__.__name__)


class MarkdownWriter(writers.Writer):
    supported = ('markdown',)
    settings_spec = ('No options here.', '', ())
    settings_defaults = {}

    output = None

    def __init__(self, builder):
        writers.Writer.__init__(self)
        self.builder = builder
        self.translator_class = self.builder.translator_class or MarkdownTranslator

    def translate(self):
        visitor = self.translator_class(self.document, self.builder)
        self.document.walkabout(visitor)
        self.output = visitor.body
