"""
Module containing code for uploading a human readable version of
RDF data to a CKAN instance.
"""

import argparse
import os
import tempfile
import requests

import ckanapi
from rdfconv.converter import RDFtoHTMLConverter


class RDFLoader(object):
    """
    Class able to convert a single nodes in an RDF file to
    a simpler representation.
     Args:
            filename: filename of the RDF file
    """
    def __init__(self, rdf_path):
        self.conv = RDFtoHTMLConverter()
        self.conv.skip_links = True
        self.conv.load_file(rdf_path)
        self.nodes = self.conv.get_nodes('en')

    def convert_node(self, rdf_about):
        """
        Convert a single node from the RDF file
        Args:
            rdf_about: unique identifier for the node

        Returns:
            An intermediate format, essentially a nested dictionary,
            of the node.
        """
        # Find the node we want
        node = None
        for cur_node in self.nodes:
            if cur_node['rdf_about'] == rdf_about:
                node = cur_node
                break

        if not node:
            # Skip the node if it's not found
            return

        return node


class CKANUploader(object):
    """
    Class for updating datasets in CKAN that have a connection to a RDF
    dataset.
    """

    def __init__(self, ckan_url, api_key):
        """
        Create the object
        Args:
            ckan_url: URL to the CKAN instance you want to update
            api_key: API key to a user that has write access to the datasets
                     you want to update

        """
        if not ckan_url.startswith(('http://', 'https://')):
            ckan_url = 'http://' + ckan_url
        self.api = ckanapi.RemoteCKAN(ckan_url, apikey=api_key)
        self._fetch_datasets()

    def _fetch_datasets(self):
        """
        Fetch all datasets that have a connection to an RDF dataset.

        """
        datasets = self.api.action.package_list()
        self.mapping = {}
        for name in datasets:
            dataset = self.api.action.package_show(id=name)
            if 'dcat_about' in dataset:
                self.mapping[dataset['dcat_about']] = name

    def update_datasets(self, rdf_path):
        """
        Update all datasets found when creating the object
        with data from given file
        Args:
            rdf_path: path to an RDF file
        """
        loader = RDFLoader(rdf_path)
        for rdf_about, ckan_name in self.mapping.iteritems():
            node = loader.convert_node(rdf_about)
            extras = self._convert_to_extras(node['attributes'])
            self._update_dataset(ckan_name, rdf_about, extras)

    def _update_dataset(self, name, rdf_about, extras):
        """
        Update a single dataset
        Args:
            name: name or id of the dataset
            rdf_about: unique identifier for the RDF node
            extras: dcat data
        """
        current_info = self.api.action.package_show(id=name)

        # We need to send the dcat id as an extra
        extras.append({
            'key': '_dcat_about_',
            'value': rdf_about
        })
        current_info['extras'] += extras

        # We also need to remove the old dcat stuff
        del current_info['dcat_fields']
        del current_info['dcat_about']

        self.api.action.package_update(**current_info)

    @staticmethod
    def _convert_to_extras(attributes):
        """
        Args:
            attributes: RDF attributes

        Returns:
            A list of extras formatted for insertion into CKAN.
        """
        extras = []
        for attribute in attributes:
            objs = []
            for obj in attribute['objs']:
                if 'link' in obj:
                    objs.append(unicode(obj['link']) + ';' + obj['title'])
                else:
                    objs.append(';' + obj['title'])

            extras.append({
                'key': '_dcat_field_' + unicode(attribute['pred_link']) +
                       ';' + attribute['pred_title'],
                'value': ';'.join(objs)
            })

        return extras


def main():
    """
    Run the uploader
    """
    # Handle arguments
    parser = argparse.ArgumentParser(
        description='CKAN RDF uploader. Converts data from a RDF file '
                    'and load it into CKAN for use with the rdf-to-html '
                    'CKAN extension',)
    parser.add_argument('ckan_url', metavar='CKAN_URL', type=str,
                        help='URL to ckan instance')
    parser.add_argument('api_key', metavar='API_KEY', type=str,
                        help='API key for a user with write access to the '
                             'datasets you want to update')
    parser.add_argument('rdf_file', metavar='RDF_FILE', type=str,
                        help='Path to the RDF file')

    args = parser.parse_args()

    temp_file = False
    if args.rdf_file.startswith(('http://', 'https://')):
        rdf_path = download_file(args.rdf_file)
        temp_file = True
    else:
        rdf_path = args.rdf_file

    uploader = CKANUploader(args.ckan_url, args.api_key)
    uploader.update_datasets(rdf_path)

    if temp_file:
        os.remove(rdf_path)


def download_file(url):
    """
    Download an RDF file from an URL
    Args:
        url: URL to the file

    Returns: filename of the downloaded file
    """
    dcat = requests.get(url)

    _, filename = tempfile.mkstemp(suffix='.rdf')
    with open(filename, 'w') as file_obj:
        file_obj.write(dcat.content)
    return filename

if __name__ == '__main__':
    main()
