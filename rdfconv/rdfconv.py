"""
This module contains code for converting RDF-files into HTML
"""
import os
import shutil
import hashlib
import codecs
from collections import OrderedDict

import rdflib
from rdflib.term import URIRef, BNode, Literal

from utils import get_link

# The RDF-types for catalogs and datasets
CATALOG = URIRef(u'http://www.w3.org/ns/dcat#Catalog')
DATASET = URIRef(u'http://www.w3.org/ns/dcat#Dataset')

# Namespaces
TYPE = u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
TITLE = u'http://purl.org/dc/terms/title'
FOAF_NAME = u'http://xmlns.com/foaf/0.1/name'
DESC = u'http://purl.org/dc/terms/description'
MOD = u'http://purl.org/dc/terms/modified'
PUBLISHER = u'http://purl.org/dc/terms/publisher'
HOMEPAGE = u'http://xmlns.com/foaf/0.1/homepage'
ISSUED = u'http://purl.org/dc/terms/issued'
MODIFIED = u'http://purl.org/dc/terms/modified'
LICENSE = u'http://purl.org/dc/terms/license'
DISTRIBUTION = u'http://www.w3.org/ns/dcat#distribution'
KEYWORD = u'http://www.w3.org/ns/dcat#keyword'

# Attributes with these namespaces are candidates for the summary
# title/description
TITLE_CANDIDATES = [TITLE, FOAF_NAME]
DESC_CANDIDATES = [DESC]

# Attributes with these namespaces will be included in the summary for a
# catalog/dataset
CATALOG_SUMMARY = [PUBLISHER, HOMEPAGE, ISSUED, MODIFIED, LICENSE]
DATASET_SUMMARY = [PUBLISHER, DISTRIBUTION, KEYWORD, ISSUED]


class RDFtoHTMLConverter(object):
    """
    Class representing a RDF to HTML converter
    """

    def __init__(self):

        # References to the underlying graph
        self._graph = None
        self._ns_mgr = None

        # Dictionary representation of the RDF file
        self.rdf_dict = {}

        # Keep track of all languages seen in the RDF
        self.languages = set()

        # Attributes that we never want output
        self.base_skip = []

        # The currently loaded file
        self.input_file = None

        # Map an RDF node to a file
        self.file_map = {}

    def load_file(self, filename):
        """
        Read RDF data from file
        """
        self.input_file = os.path.basename(filename)

        # Load graph from file
        self._graph = rdflib.Graph()
        self._graph.load(filename, format='application/rdf+xml')

        # Easy access to namespace manager
        self._ns_mgr = self._graph.namespace_manager

        # Build dictionary
        self.rdf_dict = {}
        for subj, pred, obj in self._graph:

            if subj.toPython() not in self.rdf_dict:
                self.rdf_dict[subj.toPython()] = {}
            if pred.toPython() not in self.rdf_dict[subj.toPython()]:
                self.rdf_dict[subj.toPython()][pred.toPython()] = []

            self.rdf_dict[subj.toPython()][pred.toPython()].append(obj)
            if isinstance(obj, Literal):
                if obj.language:
                    # Literals can have a language tag,
                    # Keep track of all languages encountered
                    self.languages.add(obj.language)

        # Generate a unique name for each node
        self.file_map = {}
        for key in self.rdf_dict.keys():
            self.file_map[key] = hashlib.md5(key).hexdigest()

    def output_html(self, folder):
        """
        Output each node to a separate file per language
        """
        os.mkdir(folder)
        shutil.copy('styles/style.css', folder)
        os.chdir(folder)

        for language in self.languages:
            for key, value in self.rdf_dict.iteritems():
                filename = self._get_file_link(key, language)
                with codecs.open(filename, 'w', 'utf-8') as output_file:
                    output_file.write('<html>')
                    write_head(output_file)
                    output_file.write(self._format_summary(key, value, language))

                    output_file.write(self._format_node(key, value, language))
                    output_file.write('</html>')
        self._output_summary_file()

    def _output_summary_file(self):
        """
        Output a summary file for the catalog once for each language
        """
        for language in self.languages:
            filename = os.path.splitext(self.input_file)[0]
            filename = get_file(filename, language)
            with codecs.open(filename, 'w', 'utf-8') as output_file:
                output_file.write('<html>')
                write_head(output_file)
                for key, value in self.rdf_dict.iteritems():
                    if TYPE in value and CATALOG in value[TYPE]:
                        summary = self._format_summary(key, value, language)
                        node = self._format_node(key, value, language,
                                                 include=CATALOG_SUMMARY)
                        output_file.write(summary)
                        output_file.write(node)

                output_file.write('<div class="datasets">')
                func = self._sort_by_title(language)
                sorted_items = OrderedDict(sorted(self.rdf_dict.items(),
                                                  key=func))
                for key, value in sorted_items.iteritems():
                    if TYPE in value and DATASET in value[TYPE]:
                        summary = self._format_summary(key, value, language,
                                                 title_format='<h2>%s</h2>',
                                                 desc_format='<b>%s</b>')
                        node = self._format_node(key, value, language,
                                                 include=DATASET_SUMMARY)
                        output_file.write(summary)
                        output_file.write(node)
                output_file.write('</div></html>')

    def _format_summary(self, node_name, node, language,
                        title_format='<h1>%s</h1>',
                        desc_format='<h3>%s</h3>'):
        """
        Generate a summary for an RDF node
        """
        out = '<div>'

        # Try to find something to use as a title and a description
        title = get_attribute(node, TITLE_CANDIDATES)
        desc = get_attribute(node, DESC_CANDIDATES)
        if title:
            formated = self._format_literal(title, language)
            if formated:
                link = self._get_file_link(node_name, language)
                link = get_link(link, formated[0])
                link = title_format % link
                out += '<div class="title">%s</div>' % link

        link = title_format % ('(' + node_name + ')')
        out += '<div class="id">%s</div>' % link

        if desc:
            formated = self._format_literal(desc, language)
            if formated:
                link = desc_format % formated[0]
                out += '<div class="desc">%s</div>' % link
        out += '</div>'
        return out

    def _format_node(self, node_name, node, language, include=None):
        """
        Returns a single node as a table with all:
        * Literals - formatted with the desired language
        * BNodes   - formatted as links
        * URIRefs  - formatted as links
        """
        if not include:
            include = sorted(node.keys())

        out = '<table>'
        for pred in include:
            try:
                obj_list = node[pred]
            except KeyError:
                # Skip the desired attributes if they are not present
                continue
            out += '<tr><td>'
            out += self._format_uriref(pred, language)
            out += '</td><td>'
            if obj_list and isinstance(obj_list[0], Literal):
                literals = self._format_literal(obj_list, language)
                out += '<br />'.join(literals)
            else:
                for obj in obj_list:
                    if isinstance(obj, URIRef):
                        out += self._format_uriref(obj, language)
                    elif isinstance(obj, BNode):
                        out += self._format_bnode(obj, language)

            out += '</td></tr>'
        out += '</table>'
        return out


    def _format_uriref(self, uri_ref, language, linebreak=True):
        """
        Return the HTML representation of a URIRef
        """
        # Does it point to a local asset?
        local_ref = unicode(uri_ref)
        if local_ref in self.rdf_dict:
            return self._format_bnode(uri_ref, language)

        # It seems that some URIRefs get normalized with a '<' and a '>'
        # at the start/end of the string.
        # We need to remove it
        norm = self._ns_mgr.normalizeUri(uri_ref).strip()

        if norm[0] == '<':
            norm = norm[1:]
        if norm[-1] == '>':
            norm = norm[:len(norm)-1]
        if norm[-1] == '/':
            norm = norm[:len(norm)-1]

        out = get_link(uri_ref, norm, linebreak)

        return out

    def _format_bnode(self, bnode, language):
        """
        Return the HTML representation of a BNonde
        """
        # Check if we can get a title for the bnode
        name = unicode(bnode)
        if isinstance(name, BNode):
            name = unicode(bnode.toPython())
        link = self._get_file_link(name, language)
        if name in self.rdf_dict:
            title = get_attribute(self.rdf_dict[name], TITLE_CANDIDATES)
            if title:
                cand_name = self._format_literal(title, language)
                if cand_name:
                    name = cand_name[0]

        return get_link(link, name)

    def _get_file_link(self, rdf_id, language):
        """
        Get a link to a file containing an RDF node. Returns none if the
        node could not be found in the current context
        """
        try:
            return get_file(self.file_map[unicode(rdf_id)],
                            language)
        except KeyError:
            return None

    def _format_literal(self, literals, language):
        """
        Return the HTML representation of one or more Literals.
        First try to get the specified language and if it does not exist, get
        the literals without a language tag. Finally, return literals of
        another language if there are not better match
        """
        same_lang = []
        no_lang = []
        other_lang = []

        for literal in literals:
            if literal.language == language:
                same_lang.append(literal.value)
            elif not literal.language:
                no_lang.append(literal.value)
            else:
                other_lang.append(literal.value)

        if same_lang:
            return same_lang
        if no_lang:
            return no_lang
        if other_lang:
            return other_lang

    def _sort_by_title(self, language):
        """
        Returns a function that can sort the rdf dictionary by title
        """
        def helper(tup):
            key, value = tup
            out = get_attribute(value, TITLE_CANDIDATES)
            if out:
                return self._format_literal(out, language)
            return out
        return helper

def get_attribute(node, candidates):
    """
    Gets an attribute from a list of candidates
    """
    for candidate in candidates:
        if candidate in node:
            return node[candidate]
    return None


def write_head(output_file):
    """
    Write the HTML head to given file
    """
    output_file.write('<head>')
    output_file.write('<link rel="stylesheet" type="text/css"'
                      'href="style.css">')
    output_file.write('<meta charset="UTF-8">')
    output_file.write('</head>')


def get_file(name, language):
    """
    Format a filename based on a name and a language
    """
    return '%s.html.%s.html' % (name, language)


