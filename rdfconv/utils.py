"""
Contains various utils used by the converter
"""


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
