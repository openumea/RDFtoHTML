"""
Contains code related to outputing HTML
"""
import codecs
import re
from datetime import datetime
from urllib.parse import unquote

from jinja2 import Environment, PackageLoader, select_autoescape
from rdflib.term import BNode, Literal, URIRef

from rdfconv.predicate import PredicateResolver

RDF_ABOUT = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#about")

CATALOG = URIRef("http://www.w3.org/ns/dcat#Catalog")
DATASET = URIRef("http://www.w3.org/ns/dcat#Dataset")
DISTRIBUTION = URIRef("http://www.w3.org/ns/dcat#Distribution")

OBJ_ORDER = [CATALOG, DATASET, DISTRIBUTION]


class HtmlConverter(object):
    """
    Class that converts a dictionary of RdfObjects into HTML
    """

    def __init__(self, rdf_objects, ns_mgr):
        self.objects = rdf_objects
        self._ns_mgr = ns_mgr

        # Predicate resolver
        self._pred_res = PredicateResolver()

        # Init templates
        self.skip_internal_links = False
        self.skip_literal_links = False

    def build_node_dict(self, language):
        """
        Build list of nested dictionaries to use as an intermediate
        format before rendering the HTML.

        :param language: language to convert to
        :returns: dictionary with nodes
        """
        objects = []
        for rdf_type in OBJ_ORDER:
            for obj in list(self.objects.values()):
                if obj.type == rdf_type:
                    objects.append(obj)

        for obj in list(self.objects.values()):
            if obj not in objects:
                objects.append(obj)

        nodes = []
        for obj in objects:
            node_dict = {"node_id": obj.fragment, "rdf_about": obj.id}
            summary = self._format_summary(obj, language)
            attributes = self._format_node(obj, language)

            node_dict.update(summary)
            node_dict.update({"attributes": attributes})
            nodes.append(node_dict)
        return nodes

    def output_html(self, path, language):
        """
        Output each node to a separate file per language
        :param path:
        :param language:
        :return:
        """
        nodes = self.build_node_dict(language)

        # TODO: We might want to add the timezone here
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        # import pdb; pdb.set_trace()

        env = Environment(
            loader=PackageLoader("rdfconv", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        main_template = env.get_template("main.html")
        out = main_template.render(nodes=nodes, date=date)

        with codecs.open(path, "w", "utf-8") as output_file:
            output_file.write(out)

    def _format_summary(self, rdf_obj, language):
        """
        Generate a summary for an RDF node
        """
        # Try to find something to use as a title and a description
        title = rdf_obj.get_title(language)
        desc = rdf_obj.get_description(language)
        rdf_type = rdf_obj.type

        out = {}
        if title:
            out["title"] = title

        if rdf_type:
            # Try to resolve the type
            label = self._pred_res.resolve(rdf_type.toPython(), language)
            if label:
                out["rdf_type"] = label
            else:
                out["rdf_type"] = rdf_type

        if desc:
            out["desc"] = desc

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
        pred_link, pred_title = self._format_uriref(
            RDF_ABOUT, language, skip_local=self.skip_internal_links
        )
        obj_link, obj_title = self._format_uriref(rdf_obj.id, language, skip_local=True)
        attributes.append(
            {
                "pred_link": pred_link,
                "pred_title": "About",
                "objs": [{"title": obj_title, "link": obj_link}],
            }
        )

        for pred in sorted(include):
            try:
                obj_list = rdf_obj.attributes[pred]
            except KeyError:
                # Skip the desired attributes if they are not present
                continue

            pred_link, pred_title = self._format_uriref(
                pred, language, skip_local=self.skip_literal_links
            )
            # Try to resolve the predicate to a more human readable format
            label = self._pred_res.resolve(pred_link, language)
            if label:
                pred_title = label

            objs = []
            if obj_list:
                # Add literals.
                lits = [_ for _ in obj_list if isinstance(_, Literal)]
                literals = format_literal(lits, language, self.skip_literal_links)
                objs.append({"title": " ".join(literals)})

                # Get the other objects and sort them based on their title
                new_list = []
                for obj in obj_list:
                    if obj in lits:
                        continue

                    if isinstance(obj, URIRef):
                        new_list.append(
                            self._format_uriref(obj, language, self.skip_internal_links)
                        )
                    elif isinstance(obj, BNode):
                        new_list.append(
                            self._format_bnode(obj, language, self.skip_internal_links)
                        )

                new_list = sorted(new_list, key=lambda t: t[1])

                for link, title in new_list:
                    objs.append({"link": link, "title": title})

            attributes.append(
                {
                    "pred_link": pred_link,
                    "pred_title": pred_title,
                    "objs": objs,
                }
            )

        # Add show more button
        return attributes

    def _format_uriref(self, uri_ref, language, skip_local=False):
        """
        Return the HTML representation of a URIRef
        """
        # Does it point to a local asset?
        local_ref = str(uri_ref)
        if local_ref in self.objects:
            return self._format_bnode(uri_ref, language, skip_local)

        # It seems that some URIRefs get normalized with a '<' and a '>'
        # at the start/end of the string.
        # We need to remove it
        norm = self._ns_mgr.normalizeUri(uri_ref).strip()

        if norm[0] == "<":
            norm = norm[1:]
        if norm[-1] == ">":
            norm = norm[: len(norm) - 1]
        if norm[-1] == "/":
            norm = norm[: len(norm) - 1]

        return uri_ref, norm

    def _format_bnode(self, bnode, language, skip_local=False):
        """
        Return the HTML representation of a BNonde
        """
        # Check if we can get a title for the bnode
        rdf_id = str(bnode)

        link = self._get_fragment_link(rdf_id)
        if link:
            title = self.objects[rdf_id].get_title(language)
            if not skip_local:
                return link, title
            else:
                return rdf_id, title

        return None, None

    def _get_fragment_link(self, rdf_id):
        """
        Get a link to a file containing an RDF node. Returns none if the
        node could not be found in the current context
        """
        try:
            return "#" + self.objects[str(rdf_id)].fragment

        except KeyError:
            return None


# region Literal formatting

# Characters allowed in an URL according to RDF 3986
LINK_REGEX = re.compile(
    r"(https?://[ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\-._~:/?#\[\]@!$&\'()*+,;=%%]+)"
)
TO_WHITESPACE = re.compile(r"[_-]")


def format_literal(literals, language, skip_link=False):
    """
    Return the HTML representation of one or more Literals.
    First try to get the specified language and if it does not exist, get
    the literals without a language tag. Finally, return literals of
    another language if there are not better match
    """
    same_lang = []
    no_lang = []
    other_lang = []
    if not literals:
        return ""

    for literal in literals:
        if not skip_link:
            value = _add_html_links(literal.value)
        else:
            value = literal.value

        if literal.language == language:
            same_lang.append(value)
        elif not literal.language:
            no_lang.append(value)
        else:
            other_lang.append(value)

    if same_lang:
        return sorted(same_lang)
    if no_lang:
        return sorted(no_lang)
    if other_lang:
        return sorted(other_lang)


def _add_html_links(string):
    """
    Find anything that looks like a hyperlink and convert it to an actual
    HTML link.
    """
    matches = LINK_REGEX.findall(string)
    for url in matches:
        # There is a special case when the URL is entered between parenthesis.
        # We want to remove the last character if it's a closing parenthesis
        # and if the url is preceeded by the matching opening parenthesis.
        if url[-1] == ")":
            char = _get_preceding_character(string, url)
            if char and char == "(":
                url = url[:-1]

        # If the last character is a ".", it's most likely used to end a
        # sentence rather than as part of the url. urls ending with "." are
        # not valid anyhow.
        if url[-1] == ".":
            url = url[:-1]

        display_name = url
        splits = display_name.rsplit("/", 1)
        if display_name.count("/") > 2 and len(splits) >= 2:
            display_name = splits[1]

        # Remove the URL encoding
        display_name = unquote(display_name)
        # We want the string in Unicode, not UTF-8, beacuse django seems to
        # like it this way. Encoding the string as latin-1 and decoding it
        # again seems to produce a pure unicode string.
        # FIXME: we are in python3 now... drop this?
        display_name = display_name.encode("latin-1").decode("utf-8")

        # We also want to remove underscores and such
        display_name = TO_WHITESPACE.sub(" ", display_name)

        html_link = _make_link(url, display_name)
        string = string.replace(url, html_link)

    return string


def _make_link(url, display_name):
    """
    Make a HTML link from an url and a display name
    """
    return '<a href=%s target="_blank">%s</a>' % (url, display_name)


def _get_preceding_character(string, sub_string):
    """
    Search a string for a substring and return the single character before the
    sub string
    """
    pos = string.find(sub_string) - 1
    if pos != -1:
        return string[pos]


# endregion
