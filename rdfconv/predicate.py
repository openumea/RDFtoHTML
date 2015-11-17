"""
Module containing functionallity for resolving predicate names from
third party sources.
"""
import logging
import requests
import rdflib
import StringIO

LABEL_CANDIDATES = ['http://www.w3.org/2000/01/rdf-schema#label']

# All providers don't use the correct way of supplying the rdf
# so we use this to map the inconsistencies.
URL_REMAP = {
    'http://schema.theodi.org/odrs': 'http://schema.theodi.org/odrs/index.ttl',
}

# All providers don't use xml format so here we map other formats
FORMATS = {
    'http://schema.theodi.org/odrs': 'n3',
}


class PredicateResolver(object):
    """
    Class for resolving a human readable version of an RDF predicate
    """

    def __init__(self):
        self._resolved = {}
        self._parsed = []

    def _get_from_cache(self, url, language):
        """
        Get the resolved name from the cache.
        :param url: url of the predicate
        :param language: language to use
        :return:
        """
        if url in self._resolved:
            if language in self._resolved[url]:
                # Prefered language found
                return self._resolved[url][language]
            elif 'en' in self._resolved[url]:
                # Fallback to english
                return self._resolved[url]['en']

    def resolve(self, url, language):
        """
        Try to get a human readable form of an RDF predicate.
        :param url: url of the predicate
        :param language: language to use
        :return:
        """
        # Do we have it cached?
        cached = self._get_from_cache(url, language)
        if cached:
            return cached

        # Fetch it from the remote specification
        self.get_rdf(url)

        # It should now be present in the cache
        return self._get_from_cache(url, language)

    def get_rdf(self, url):
        """
        :param url:
        :return:
        """
        # Most providers use # or / for delimiting the identifier from the
        # actual download url
        if '#' in url:
            url = url.rsplit('#', 1)[0]
        elif '/' in url:
            url = url.rsplit('/', 1)[0]

        # Have we already downloaded and this url?
        if url in self._parsed:
            return

        headers = {'Accept': 'application/rdf+xml'}

        # Some URLs we've encountered do not provide xml versions of the rdf
        if url in FORMATS:
            rdf_format = FORMATS[url]
        else:
            rdf_format = 'xml'

        # Some URLs also do not follow the standard way of requesting a
        # the resource on a different format. They do however provide
        # the resource but at a differnt URL.
        if url in URL_REMAP:
            url = URL_REMAP[url]

        logging.info('Downloading %s', url)
        try:
            resp = requests.get(url, headers=headers)
        except Exception as err:  # pylint: disable=W0703
            # We want to catch all exceptions here
            logging.warning('Unable to download %s. %s', url, err.message)
            return

        file_obj = StringIO.StringIO()
        file_obj.write(resp.text.encode('utf-8'))
        file_obj.seek(0)

        graph = rdflib.Graph()
        try:
            graph.load(file_obj, format=rdf_format)
        except Exception as err:  # pylint: disable=W0703
            # We want to catch all exceptions here
            logging.warning('Unable to parse file: %s. %s', url, err.message)
        for subj, pred, obj in graph:

            if isinstance(obj, rdflib.Literal) and unicode(pred) in LABEL_CANDIDATES:
                subj = unicode(subj)
                if subj not in self._resolved:
                    self._resolved[subj] = {}
                if obj.language:
                    language = obj.language
                else:
                    language = 'en'
                self._resolved[subj][language] = unicode(obj.value).title()

        self._parsed.append(url)
