"""
This module contains code for converting RDF-files into HTML
"""
import os
import sys
import hashlib

import rdflib
from rdflib.term import URIRef, BNode, Literal

from utils import get_link

TYPE_NS = u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'

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

        # Keep track of which file contain which node
        self.file_map = {}

    def load_file(self, filename):
        """
        Read RDF data from file
        """
        # Load graph from file
        self._graph = rdflib.Graph()
        self._graph.load(filename, format='application/rdf+xml')

        # Easy access to namespace manager
        self._ns_mgr = self._graph.namespace_manager

        self.rdf_dict = {}

        # Build dictionary
        for subj, pred, obj in self._graph:

            if subj.toPython() not in self.rdf_dict:
                self.rdf_dict[subj.toPython()] = {}
            if pred.toPython() not in self.rdf_dict[subj.toPython()]:
                self.rdf_dict[subj.toPython()][pred.toPython()] = {}

            language = 'no-lang'
            if isinstance(obj, Literal):
                # Literals can have a language tag,
                # so we same them in a dictionary
                if obj.language:
                    # Keep track of all languages encountered
                    self.languages.add(obj.language)
                    language = obj.language
                self.rdf_dict[subj.toPython()][pred.toPython()][language] = obj
            else:
                self.rdf_dict[subj.toPython()][pred.toPython()] = obj

        # Generate a unique name for each node
        self.file_map = {}
        for key in self.rdf_dict.keys():
            self.file_map[key] = hashlib.md5(key).hexdigest()

    def output_html(self, folder):
        """
        Output contents of the RDF graph to separate files
        """

        if os.path.exists(folder):
            print 'Folder already exists, exiting.'
            sys.exit(1)
        else:
            os.makedirs(folder)

        os.chdir(folder)

        # Create a separate dir for every language encountered
        for language in self.languages:
            os.makedirs(language)
            for key, val in self.rdf_dict.iteritems():
                with open(language + '/' + self.file_map[key], 'w') as current_file:
                    self._output_node(key, val, current_file, language)

        self._create_index_pages()

    def _create_index_pages(self):
        # Create an index file in each language referencing each node
        for language in self.languages:
            with open(language + '/index.html', 'w') as index_file:
                index_file.write('<html><table>')
                index_file.write('<tr><th>Type</th><th>Resource</th></tr>')
                for key, value in self.rdf_dict.iteritems():
                    index_file.write('<tr>')
                    index_file.write('<td>')
                    if TYPE_NS in value:
                        index_file.write(self._format_uriref(value[TYPE_NS], linebreak=False))
                    else:
                        index_file.write('Unknown')
                    index_file.write('</td>')
                    index_file.write('<td>')
                    index_file.write(get_link(self.file_map[key], key))
                    index_file.write('</td>')
                    index_file.write('</tr>')
                index_file.write('</table></html>')

        # Create a master index file with reference to each language
        with open('index.html', 'w') as index_file:
            index_file.write('<html>')
            for language in self.languages:
                index_file.write(get_link(language + '/index.html', language))
            index_file.write('</html>')



    def _output_node(self, node_name, node, file_obj, language):
        """
        Output one node in the RDF graph to a single file
        """
        file_obj.write('<html>')
        file_obj.write('<head>')
        file_obj.write('<meta charset="UTF-8">')
        file_obj.write('</head>')
        file_obj.write('<h3>' + node_name + '</h3>')
        file_obj.write('<table style="table-layout: fixed;">')
        for pred, obj in node.iteritems():
            file_obj.write('<tr>')
            file_obj.write('<td>',)
            file_obj.write(self._format_uriref(pred))
            file_obj.write('</td>')
            file_obj.write('<td>')
            # file_obj.write(the objects.

            if isinstance(obj, URIRef):
                file_obj.write(self._format_uriref(obj))
            elif isinstance(obj, BNode):
                file_obj.write(self._format_bnode(obj))
            elif isinstance(obj, dict):
                file_obj.write(self._format_literal(obj, language))

            file_obj.write('</td>')
            file_obj.write('</tr>')
        file_obj.write('</table>')
        file_obj.write('</html>')

    def _format_literal(self, in_dict, language):
        """
        Return the HTML representation of a Literal
        """
        # Return desired language if exists
        if language in in_dict.keys():
            return in_dict[language].encode('utf-8')

        # Check if there is any non-language specific data
        if 'no-lang' in in_dict.keys():
            return in_dict['no-lang'].encode('utf-8')

        # No data to return
        return ''

    def _format_uriref(self, uri_ref, linebreak=True):
        """
        Return the HTML representation of a URIRef
        """
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

        return out.encode('utf-8')

    def _format_bnode(self, bnode):
        """
        Return the HTML representation of a BNonde
        """
        out = get_link(self.file_map[bnode.toPython()], bnode)
        return out.encode('utf-8')


