# -*- coding: utf-8 -*-
"""
    sphinx.builders.text
    ~~~~~~~~~~~~~~~~~~~~

    Plain-text Sphinx builder.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import codecs
from os import path

from docutils import nodes
from docutils.io import StringOutput
from six import iteritems, text_type, string_types

from sphinx.builders import Builder
from sphinx.util.console import bold, darkgreen, brown
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util.osutil import ensuredir, os_path
from sphinx.writers.markdown import MarkdownWriter


class MarkdownBuilder(Builder):
    name = 'markdown'
    format = 'markdown'
    out_suffix = '.md'
    allow_parallel = False

    def prepare_writing(self, docnames):
        self.writer = MarkdownWriter(self)

    def write_doc(self, docname, doctree):
        self.current_docname = docname
        destination = StringOutput(encoding='utf-8')
        self.writer.write(doctree, destination)
        outfilename = path.join(self.outdir, os_path(docname) + self.out_suffix)
        ensuredir(path.dirname(outfilename))
        try:
            f = codecs.open(outfilename, 'w', 'utf-8')
            try:
                f.write(self.writer.output)
            finally:
                f.close()
        except (IOError, OSError) as err:
            self.warn("error writing file %s: %s" % (outfilename, err))

    def finish(self):
        pass

    # single html

    def get_outdated_docs(self):
        return 'all documents'

    def get_target_uri(self, docname, typ=None):
        if docname in self.env.all_docs:
            # all references are on the same page...
            return self.config.master_doc + self.out_suffix + \
                '#document-' + docname
        else:
            # chances are this is a html_additional_page
            return docname + self.out_suffix

    def get_relative_uri(self, from_, to, typ=None):
        # ignore source
        return self.get_target_uri(to, typ)

    def fix_refuris(self, tree):
        # fix refuris with double anchor
        fname = self.config.master_doc + self.out_suffix
        for refnode in tree.traverse(nodes.reference):
            if 'refuri' not in refnode:
                continue
            refuri = refnode['refuri']
            hashindex = refuri.find('#')
            if hashindex < 0:
                continue
            hashindex = refuri.find('#', hashindex+1)
            if hashindex >= 0:
                refnode['refuri'] = fname + refuri[hashindex:]

    def assemble_doctree(self):
        master = self.config.master_doc
        tree = self.env.get_doctree(master)
        tree = inline_all_toctrees(self, set(), master, tree, darkgreen)
        tree['docname'] = master
        self.env.resolve_references(tree, master, self)
        self.fix_refuris(tree)
        return tree

    def assemble_toc_secnumbers(self):
        # Assemble toc_secnumbers to resolve section numbers on SingleHTML.
        # Merge all secnumbers to single secnumber.
        #
        # Note: current Sphinx has refid confliction in singlehtml mode.
        #       To avoid the problem, it replaces key of secnumbers to
        #       tuple of docname and refid.
        #
        #       There are related codes in inline_all_toctres() and
        #       HTMLTranslter#add_secnumber().
        new_secnumbers = {}
        for docname, secnums in iteritems(self.env.toc_secnumbers):
            for id, secnum in iteritems(secnums):
                new_secnumbers[(docname, id)] = secnum

        return {self.config.master_doc: new_secnumbers}

    def get_doc_context(self, docname, body, metatags):
        # no relation links...
        toc = self.env.get_toctree_for(self.config.master_doc, self, False)
        # if there is no toctree, toc is None
        if toc:
            self.fix_refuris(toc)
            toc = self.render_partial(toc)['fragment']
            display_toc = True
        else:
            toc = ''
            display_toc = False
        return dict(
            parents = [],
            prev = None,
            next = None,
            docstitle = None,
            title = self.config.html_title,
            meta = None,
            body = body,
            metatags = metatags,
            rellinks = [],
            sourcename = '',
            toc = toc,
            display_toc = display_toc,
        )

    def write(self, *ignored):
        docnames = self.env.all_docs

        self.info('preparing documents... ', nonl=True)
        self.prepare_writing(docnames)
        self.info('done')

        self.info('assembling single document... ', nonl=True)
        doctree = self.assemble_doctree()
        self.env.toc_secnumbers = self.assemble_toc_secnumbers()
        self.info()
        self.info('writing... ', nonl=True)
        self.write_doc_serialized(self.config.master_doc, doctree)
        self.write_doc(self.config.master_doc, doctree)
        self.info('done')
