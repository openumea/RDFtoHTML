"""
Contains various utils used by the converter
"""
import urllib2
import re

# Characters allowed in an URL according to RDF 3986
LINK_REGEX = re.compile(r'(http://[ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\-._~:/?#\[\]@!$&\'()*+,;=%%]+)')
TO_WHITESPACE = re.compile(r'[_-]')

def format_literal(literals, language):
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
        return ''

    for literal in literals:
        value = add_html_links(literal.value)
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


def add_html_links(string):
    matches = LINK_REGEX.findall(string)
    for url in matches:
        # There is a special case when the URL is entered between parenthesis.
        # We want to remove the last character if it's a closing parenthesis and
        # if the url is preceeded by the matching opening parenthesis.
        if url[-1] == ')':
            char = get_preceding_character(string, url)
            if char and char == '(':
                url = url[:-1]

        # If the last character is a ".", it's most likely used to end a
        # sentence rather than as part of the url. urls ending with "." are not valid anyhow.
        if url[-1] == '.':
            url = url[:-1]

        display_name = url
        splits = display_name.rsplit('/', 1)
        if display_name.count('/') > 2 and len(splits) >= 2:
            display_name = splits[1]

        # Remove the URL encoding
        display_name = urllib2.unquote(display_name)
        # We want the string in Unicode, not UTF-8, beacuse django seems to like it this way.
        # Encoding the string as latin-1 and decoding it again seems to produce a pure unicode string.
        display_name = display_name.encode('latin-1').decode('utf-8')

        # We also want to remove underscores and such
        display_name = TO_WHITESPACE.sub(' ', display_name)

        html_link = make_link(url, display_name)
        string = string.replace(url, html_link)

    return string


def get_attribute(node, candidates):
    """
    Gets an attribute from a list of candidates
    """
    if not isinstance(candidates, list):
        candidates = [candidates]
    for candidate in candidates:
        if candidate in node:
            return node[candidate]
    return None


def get_file(name, language):
    """
    Format a filename based on a name and a language
    """
    return '%s.html.%s' % (name, language)

def make_link(url, display_name):
    return u'<a href=%s>%s</a>' % (url, display_name)


def get_preceding_character(string, sub_string):
    pos = string.find(sub_string) - 1
    if pos != -1:
        return string[pos]
