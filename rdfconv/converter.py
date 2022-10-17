"""
This module contains code for converting RDF-files into HTML
"""
import logging
import os
import shutil
from collections import OrderedDict
from pathlib import Path

import rdflib
from rdflib.term import Literal

from rdfconv.html import HtmlConverter
from rdfconv.objects import RdfObject

if not logging:
    # rdflib requires a logger to be setup
    logging.basicConfig()


class Error(Exception):
    """
    Base class for exceptions in this module
    """


class LanguageError(Error):
    """
    Raised when the specified languages differ from the actual languages
    encountered in the RDF file.
    """

    def __init__(self, filename, specified, actual):
        super(LanguageError, self).__init__()
        error = (
            "Languages encountered in RDF file differ from specified "
            "languages %s.\n\t" + "Specified: %s\n\t" + "Actual:    %s"
        )

        specified = ",".join(sorted(specified))
        actual = ",".join(sorted(actual))

        self.msg = error % (filename, specified, actual)

    def __str__(self):
        return self.msg


class RDFtoHTMLConverter(object):
    """
    Class representing a RDF to HTML converter
    """

    def __init__(self, languages=None, config=None):
        if not languages:
            languages = ["all"]
        self.config = config or {}
        # References to the underlying graph
        self._graph = None
        self._ns_mgr = None

        # Dictionary representation of the RDF file
        self.objects = OrderedDict()

        # Keep track of all languages seen in the RDF
        self.languages = set()

        # Keep track of desired languages
        self.specified_languages = set(languages)

        # The currently loaded file
        self.input_file = None

        self._skip_links = False

    @property
    def skip_links(self):
        """
        Should the converter skip converting stuff that looks like links
        to actual HTML links?
        :return:
        """
        return self._skip_links

    @skip_links.setter
    def skip_links(self, value):
        """
        Tells the converter where to skip converting what looks like
        links to actual HTML links
        :param value:
        :return:
        """
        self._skip_links = value

    def load_file(self, filename):
        """
        Read RDF data from file
        """
        self.input_file = os.path.basename(filename)

        # Load graph from file
        self._graph = rdflib.Graph()
        self._graph.parse(filename, format="text/turtle")

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
        for key, value in rdf_dict.items():
            obj = RdfObject(key, value, self._ns_mgr)
            objects.append(obj)

        # Sort them by type -> title
        self.objects = OrderedDict()
        for obj in sorted(objects, key=lambda x: x.get_sort_tuple("en")):
            self.objects[obj.id] = obj

        self._validate_languages()

    def output_html(self, folder, index_html=False):
        """
        Output one file per language encountered in the rdf file
        """
        if not os.path.exists(folder):
            os.mkdir(folder)
        elif not os.path.isdir(folder):
            logging.error("Could not write output. %s is not a directory.", folder)
            exit(1)

        # Move script and style files
        base_dir = os.path.dirname(os.path.abspath(__file__))
        for filename in ["style.css", "rdfconv.js"]:
            dpath = Path(folder) / filename
            if dpath.exists():
                continue
            shutil.copyfile(Path(base_dir) / "includes" / filename, dpath)

        html_conv = HtmlConverter(
            self.objects, self._ns_mgr, local_ns=self.config.get("local_ns")
        )
        if self.skip_links:
            html_conv.skip_literal_links = True
            html_conv.skip_internal_links = True

        if index_html:
            filename = "index.html"
            path = os.path.join(folder, filename)
            html_conv.output_html(path, "en")
            return

        # Assume english if no language was encountered
        if not self.languages:
            self.languages.add("en")
        for language in self.languages:
            filename = "%s.%s.html" % (os.path.splitext(self.input_file)[0], language)
            path = os.path.join(folder, filename)
            html_conv.output_html(path, language)

    def get_nodes(self, language):
        """
        Get the nodes parsed from the RDF file

        This is used before running the actual HTML conversion
        and can be used by other software that wants to render
        their own version of the data.
        :param language:
        :return: a list of nested dictionaries with information
                 about each node in the RDF file
        """
        html_conv = HtmlConverter(self.objects, self._ns_mgr)
        if self.skip_links:
            html_conv.skip_literal_links = True
            html_conv.skip_internal_links = True
        return html_conv.build_node_dict(language)

    def _validate_languages(self):
        """
        Make sure the languages specified by the user are the same as those
        encountered in the RDf file.
        """
        if "all" in self.specified_languages:
            return

        if self.languages != self.specified_languages:
            raise LanguageError(
                self.input_file, self.specified_languages, self.languages
            )
