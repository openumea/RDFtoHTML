"""
Contains various utils used by the converter
"""

def get_link(link_to, display_value, linebreak=True):
    """
    Get a html link
    """
    out = '<a href=%s>%s</a>' % (link_to, display_value)
    if linebreak:
        out += '<br />'
    return out


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
    return '%s.html.%s.html' % (name, language)
