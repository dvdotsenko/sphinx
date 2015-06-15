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
FIRST = 0
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

    def visit_Text(self, node):
        self.add_text(node.astext())

    def depart_Text(self, node):
        pass

    def new_state(self, indent=STDINDENT):
        self.states.append([])
        self.stateindent.append(indent)

    def end_state(self, wrap=True, end=NotSet, first=None, wrap_fn=None):
        """

        :param wrap:
        :param end:
        :type end: None or list or NotSet
        :param first:
        :param wrap_fn:
        :return:
        """

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

        if wrap_fn:
            result = wrap_fn(result)

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

    @property
    def _title_prefix(self):
        if self.sectionlevel:
            return (u'#' * self.sectionlevel) + ' '
        else:
            return ''

    def visit_section(self, node):
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
                    '{}{}'.format(title_prefix, title),
                    ''
                ]
            )
        )

    def visit_paragraph(self, node):
        if not isinstance(node.parent, nodes.Admonition) or \
                isinstance(node.parent, addnodes.seealso):

            self.new_state(0)

    def depart_paragraph(self, node):
        if not isinstance(node.parent, nodes.Admonition) or \
                isinstance(node.parent, addnodes.seealso):

            self.end_state()

    def visit_compound(self, node):
        pass

    def depart_compound(self, node):
        pass

    def visit_literal_block(self, node):
        # This is "code" section
        self.new_state()

    def depart_literal_block(self, node):
        def _wrap_fn(content):
            """
            :param list content: [(0, [u'code line 1', u'code line 2', ''])]
            :return: same with tripple-backticks wrapping around code lines array
            """
            if content:
                content_group = content[FIRST]
                lines = content_group[LAST]
                lines.insert(FIRST, '```')
                lines.insert(LAST, '```') # the very last line is empty spacer.
            return content
        self.end_state(wrap_fn=_wrap_fn)

    def visit_reference(self, node):
        # these are single backticks, inline
        # while in pure rst these are "reference to some other object"
        # we are habitually using them in Markdown-like inline-code block
        self.add_text('`')

    def depart_reference(self, node):
        self.add_text('`')

    def visit_title_reference(self, node):
        self.add_text('`')

    def depart_title_reference(self, node):
        self.add_text('`')

    def visit_desc(self, node):
        # top-level entry for function definitions block
        pass

    def depart_desc(self, node):
        pass

    def visit_desc_signature(self, node):
        # parent node for method / class / function signature line
        # it's just a grouping element. See individual parts below for rendering of name, addname, args etc
        self.new_state(0)
        self.add_text(self.nl + '#' + self._title_prefix)
        if node.parent['objtype'] in ('class', 'exception'):
            self.add_text('%s ' % node.parent['objtype'])

    def depart_desc_signature(self, node):
        self.end_state(wrap=False, end=None)

    def visit_desc_name(self, node):
        # actual name of the function
        # we just wrap it in "bold"
        self.add_text('**`')

    def depart_desc_name(self, node):
        self.add_text('`**')

    def visit_desc_addname(self, node):
        # module / lib prefix to the name of the function (if specified)
        self.add_text('`')

    def depart_desc_addname(self, node):
        self.add_text('`')

    def visit_desc_parameterlist(self, node):
        # this is a parent for a list of function params
        self.add_text('(')
        args = node.astext()
        if args:
            self.add_text(
                u'_`{}`_'.format(args)
            )
        raise nodes.SkipChildren

    def depart_desc_parameterlist(self, node):
        self.add_text(')')

    def visit_desc_content(self, node):
        # start of docstring / actual body of the function description goes here
        self.new_state()
        self.add_text('')

    def depart_desc_content(self, node):
        self.end_state()

    def visit_emphasis(self, node):
        self.add_text('_')

    def depart_emphasis(self, node):
        self.add_text('_')

    def visit_literal_emphasis(self, node):
        self.add_text('_')

    def depart_literal_emphasis(self, node):
        self.add_text('_')

    def visit_strong(self, node):
        self.add_text('**')

    def depart_strong(self, node):
        self.add_text('**')

    def visit_literal_strong(self, node):
        self.add_text('**')

    def depart_literal_strong(self, node):
        self.add_text('**')

    def unknown_visit(self, node):
        self.builder.info(u'== ({}) skipping: {} - "{}"'.format(
            self.sectionlevel,
            node.__class__.__name__,
            node.astext()
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
