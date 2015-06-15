def get_link(link_to, display_value, linebreak=True):
    out = '<a href=%s>%s</a>'  % (link_to, display_value)
    if linebreak:
        out += '<br />'
    return out
