"""
This module contains code for converting RDF-files into HTML
"""
import os
import sys
import logging
import shutil
from collections import OrderedDict

import rdflib
from rdflib.term import Literal

from utils import get_file
from htmlconv import HtmlConverter
from rdf_object import RdfObject

# rdflib requires a logger to be setup
logging.basicConfig()


class RDFtoHTMLConverter(object):
    """
    Class representing a RDF to HTML converter
    """

    def __init__(self):

        # References to the underlying graph
        self._graph = None
        self._ns_mgr = None

        # Dictionary representation of the RDF file
        self.objects = OrderedDict()

        # Keep track of all languages seen in the RDF
        self.languages = set()

        # The currently loaded file
        self.input_file = None

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
        rdf_dict = {}
        for subj, pred, obj in self._graph:

            if subj.toPython() not in rdf_dict:
                rdf_dict[subj.toPython()] = {}
            if pred.toPython() not in rdf_dict[subj.toPython()]:
                rdf_dict[subj.toPython()][pred.toPython()] = []

            rdf_dict[subj.toPython()][pred.toPython()].append(obj)
            if isinstance(obj, Literal):
                if obj.language:
                    # Literals can have a language tag,
                    # Keep track of all languages encountered
                    self.languages.add(obj.language)

        # Generate objects
        objects = []
        for key, value in rdf_dict.iteritems():
            obj = RdfObject(key, value, self._ns_mgr)
            objects.append(obj)

        # Sort them by type -> title
        self.objects = OrderedDict()
        for obj in sorted(objects, key=lambda x: x.get_sort_tuple('en')):
            self.objects[obj.id] = obj

    def output_html(self, folder):
        """
        Output one file per language encountered in the rdf file
        """
        if not os.path.exists(folder):
            os.mkdir(folder)
        elif not os.path.isdir(folder):
            print folder, 'is not a directory'
            exit(1)

        # Move script and style files
        shutil.copy('includes/style.css', folder)
        shutil.copy('includes/rdfconv.js', folder)
        os.chdir(folder)

        html_conv = HtmlConverter(self.objects, self._ns_mgr)
        for language in self.languages:
            filename = os.path.splitext(self.input_file)[0]
            filename = get_file(filename, language)

            html_conv.output_html(filename, language)


def main(input_file, output_folder):
    """
    Run the RDF converter
    """
    rdf_conv = RDFtoHTMLConverter()
    rdf_conv.load_file(input_file)
    rdf_conv.output_html(output_folder)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: main.py DCAT_INPUT_FILE OUTPUT_FOLDER'
        sys.exit(0)
    main(sys.argv[1], sys.argv[2])
