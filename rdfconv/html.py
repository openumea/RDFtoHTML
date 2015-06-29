"""
Contains code related to outputing HTML
"""
import codecs
from rdflib.term import URIRef, BNode, Literal
from django.template import Context
from django.template.loader import get_template
from django.conf import settings

from rdfconv.utils import format_literal

RDF_ABOUT = URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#about')

CATALOG = URIRef(u'http://www.w3.org/ns/dcat#Catalog')
DATASET = URIRef(u'http://www.w3.org/ns/dcat#Dataset')
DISTRIBUTION = URIRef(u'http://www.w3.org/ns/dcat#Distribution')

OBJ_ORDER = [CATALOG, DATASET, DISTRIBUTION]


class HtmlConverter(object):
    """
    Class that converts a dictionary of RdfObjects into HTML
    """

    def __init__(self, rdf_objects, ns_mgr):
        self.objects = rdf_objects
        self._ns_mgr = ns_mgr

        # Init templates

        settings.configure(
            TEMPLATE_DIRS=('templates',),
            TEMPLATE_LOADERS=("django.template.loaders.filesystem.Loader",),
            TEMPLATE_DEBUG=True)

    def output_html(self, path, language):
        """
        Output each node to a separate file per language
        """
        objects = []
        for rdf_type in OBJ_ORDER:
            for obj in self.objects.values():
                if obj.type == rdf_type:
                    objects.append(obj)

        for obj in self.objects.values():
            if obj not in objects:
                objects.append(obj)

        main_template = get_template('main.html')

        nodes = []
        for obj in objects:
            node_dict = {'node_id': obj.fragment}
            summary = self._format_summary(obj, language)
            attributes = self._format_node(obj, language)

            node_dict.update(summary)
            node_dict.update({'attributes': attributes})

            nodes.append(node_dict)

        with codecs.open(path, 'w', 'utf-8') as output_file:
            context = Context({'nodes': nodes})
            out = main_template.render(context)
            output_file.write(out)

    def _format_summary(self, rdf_obj, language):
        """
        Generate a summary for an RDF node
        """
        # Try to find something to use as a title and a description
        title = rdf_obj.get_title(language)
        desc = rdf_obj.get_description(language)
        rdf_type = rdf_obj.get_canoical_type()

        out = {}
        if title:
            out['title'] = title

        if rdf_type:
            out['title'] = rdf_type

        if desc:
            out['desc'] = desc

        return out

    def _format_node(self, rdf_obj, language, include=None):
        """
        Returns a single node as a table with all:
        * Literals - formatted with the desired language
        * BNodes   - formatted as links
        * URIRefs  - formatted as links
        """
        if not include:
            include = sorted(rdf_obj.attributes.keys())

        attributes = []
        # Add the RDF id att the top
        pred_link, pred_title = self._format_uriref(RDF_ABOUT, language)
        attributes.append({
            'pred_link': pred_link,
            'pred_title': pred_title,
            'objs': [self._format_uriref(rdf_obj.id, language,
                                         skip_local=True)],
        })

        for pred in sorted(include):
            try:
                obj_list = rdf_obj.attributes[pred]
            except KeyError:
                # Skip the desired attributes if they are not present
                continue
            pred_link, pred_title = self._format_uriref(pred, language)

            objs = []
            if obj_list and isinstance(obj_list[0], Literal):
                literals = format_literal(obj_list, language)
                objs.append((' '.join(literals), None))
            else:
                # Get the other objects and sort them based on their title
                new_list = []
                for obj in obj_list:
                    if isinstance(obj, URIRef):
                        new_list.append(self._format_uriref(obj, language))
                    elif isinstance(obj, BNode):
                        new_list.append(self._format_bnode(obj, language))

                new_list = sorted(new_list, key=lambda t: t[1])

                for link, value in new_list:
                    obj_link = link
                    obj_title = value
                    objs.append((obj_link, obj_title))

            attributes.append({
                'pred_link': pred_link,
                'pred_title': pred_title,
                'objs': objs,

            })

        # Add show more button
        return attributes

    def _format_uriref(self, uri_ref, language, skip_local=False):
        """
        Return the HTML representation of a URIRef
        """
        # Does it point to a local asset?
        local_ref = unicode(uri_ref)
        if not skip_local and local_ref in self.objects:
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

        return uri_ref, norm

    def _format_bnode(self, bnode, language):
        """
        Return the HTML representation of a BNonde
        """
        # Check if we can get a title for the bnode
        rdf_id = unicode(bnode)
        link = self._get_fragment_link(rdf_id)
        if link:
            title = self.objects[rdf_id].get_title(language)
            return link, title

        return (None, None)

    def _get_fragment_link(self, rdf_id):
        """
        Get a link to a file containing an RDF node. Returns none if the
        node could not be found in the current context
        """
        try:
            return '#' + self.objects[unicode(rdf_id)].fragment

        except KeyError:
            return None
