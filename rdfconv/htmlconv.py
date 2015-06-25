"""
Contains code related to outputing HTML
"""
import codecs

from rdflib.term import URIRef, BNode, Literal

from utils import get_link, format_literal


class HtmlConverter(object):
    """
    Class that converts a dictionary of RdfObjects into HTML
    """

    def __init__(self, rdf_objects, ns_mgr):
        self.objects = rdf_objects
        self._ns_mgr = ns_mgr

    def output_html(self, path, language):
        """
        Output each node to a separate file per language
        """

        with codecs.open(path, 'w', 'utf-8') as output_file:
            output_file.write('<html>')
            write_head(output_file)
            for rdf_id, obj in self.objects.iteritems():
                output_file.write('<div class="rdf_obj" id="%s">' % obj.fragment)
                summary = self._format_summary(obj, language)
                node = self._format_node(obj, language)
                output_file.write(summary)
                output_file.write(node)
                output_file.write('</div>')

            output_file.write('</html>')

    def _format_summary(self, rdf_obj, language):
        """
        Generate a summary for an RDF node
        """
        out = ''
        # Try to find something to use as a title and a description
        title = rdf_obj.get_title(language)
        desc = rdf_obj.get_description(language)
        rdf_type = rdf_obj.get_canoical_type()

        if title:
            out += '<div class="title"><h1>%s</h1></div>' % title

        out += '<div class="rdf_id"><h1>%s</h1></div>' % rdf_obj.id

        if rdf_type:
            out += '<div class="type"><h2>%s</h2></div>' % rdf_type

        if desc:
            out += '<div class="desc">%s</div>' % desc

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

        out = '<div class="full_info"><table>'
        for pred in include:
            try:
                obj_list = rdf_obj.attributes[pred]
            except KeyError:
                # Skip the desired attributes if they are not present
                continue
            out += '<tr><td>'
            out += self._format_uriref(pred, language)
            out += '</td><td>'
            if obj_list and isinstance(obj_list[0], Literal):
                literals = format_literal(obj_list, language)
                out += '<br />'.join(literals)
            else:
                for obj in obj_list:
                    if isinstance(obj, URIRef):
                        out += self._format_uriref(obj, language)
                    elif isinstance(obj, BNode):
                        out += self._format_bnode(obj, language)

            out += '</td></tr>'
        out += '</table></div>'

        # Add show more button
        out += '<a class="show_more">Show more</a>'
        return out

    def _format_uriref(self, uri_ref, language):
        """
        Return the HTML representation of a URIRef
        """
        # Does it point to a local asset?
        local_ref = unicode(uri_ref)
        if local_ref in self.objects:
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

        out = get_link(uri_ref, norm)

        return out

    def _format_bnode(self, bnode, language):
        """
        Return the HTML representation of a BNonde
        """
        # Check if we can get a title for the bnode
        rdf_id = unicode(bnode)
        link = self._get_fragment_link(rdf_id)
        if link:
            title = self.objects[rdf_id].get_title(language)
            return get_link(link, title)

        return None

    def _get_fragment_link(self, rdf_id):
        """
        Get a link to a file containing an RDF node. Returns none if the
        node could not be found in the current context
        """
        try:
            return '#' + self.objects[unicode(rdf_id)].fragment

        except KeyError:
            return None


def write_head(output_file):
    """
    Write the HTML head to given file
    """
    output_file.write('<head>')
    output_file.write('<link rel="stylesheet" type="text/css"'
                      'href="style.css">')
    output_file.write('<meta charset="UTF-8">')
    write_js(output_file)
    output_file.write('</head>')


def write_js(output_file):
    """
    Write the JavaScript to given file
    """
    java_script = '''
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <script>
    $(document).ready(function() {
        $('.rdf_obj .show_more').click(function() {
            var link = $(this);
            table = $(this).siblings('.full_info');
            table.slideToggle(400, function() {
                if (table.is(':visible')) {
                    link.html('Show less');
                } else {
                    link.html('Show more');
                }
            })

        });


    });
    </script>
    '''

    output_file.write(java_script)
