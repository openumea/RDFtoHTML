"""
Class containing code related to RDF objects
"""

import hashlib
from rdfconv.utils import get_attribute
from rdfconv.html import format_literal

# Namespaces
TYPE = u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
TITLE = u'http://purl.org/dc/terms/title'
FOAF_NAME = u'http://xmlns.com/foaf/0.1/name'
LABEL = u'http://www.w3.org/2000/01/rdf-schema#label'
VCARD_NAME = u'http://www.w3.org/2006/vcard/ns#fn'
DESC = u'http://purl.org/dc/terms/description'

# Attributes with these namespaces are candidates for the summary
# title/description
TITLE_CANDIDATES = [TITLE, FOAF_NAME, LABEL, VCARD_NAME]
DESC_CANDIDATES = [DESC]


class RdfObject(object):
    """
    Class representing an rdf object.
    Contains methods for easily accessing common attributes
    """

    def __init__(self, id, attributes, ns_mgr=None):

        # Rdf type
        self.type = None

        # Rdf id
        self.id = id

        # Fragment id
        self.fragment = hashlib.md5(id).hexdigest()

        # List of potential titles and descriptions
        self.title = None
        self.description = None

        # Other attributes
        self.attributes = attributes

        # Try to find a type
        types = get_attribute(attributes, [TYPE])
        if types:
            self.type = types[0]

        # Get a list of potential titles and descriptions
        self.title = get_attribute(attributes, TITLE_CANDIDATES)
        self.description = get_attribute(attributes, DESC_CANDIDATES)

        # Reference to a ns manager
        self._ns_mgr = ns_mgr

    def __repr__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

    def get_title(self, language):
        """
        Gets the title of the RDF object
        """
        candidates = format_literal(self.title, language)
        if candidates:
            return candidates[0]
        else:
            return self.id

    def get_description(self, language):
        """
        Gets the description of the RDF object
        """
        candidates = format_literal(self.description, language)
        if candidates:
            return candidates[0]
        return ''

    def get_canoical_type(self):
        """
        Gets the shortened type of the RDF object
        """
        if not self.type:
            return ''
        norm = self._ns_mgr.normalizeUri(self.type).strip()

        if norm[0] == '<':
            norm = norm[1:]
        if norm[-1] == '>':
            norm = norm[:len(norm)-1]
        if norm[-1] == '/':
            norm = norm[:len(norm)-1]
        return norm

    def get_sort_tuple(self, language):
        """
        Get the sort order of the object
        """
        return (self.get_canoical_type(), self.get_title(language))
