"""
Main entry point
"""

import sys
import os
import argparse
from rdfconv.loader import RDFtoHTMLConverter


def main(input_file, output_folder):
    """
    Run the RDF converter
    """
    rdf_conv = RDFtoHTMLConverter()
    rdf_conv.load_file(input_file)
    rdf_conv.output_html(output_folder)


def gen_index(output_folder):

    files = []
    for f in os.listdir(output_folder):
        if f == 'index.html' or f.startswith('.'):
            continue
        file_path = os.path.join(output_folder, f)
        if os.path.isfile(file_path) and 'html' in f:
            files.append(f)

    path = os.path.join(output_folder, 'index.html')
    with open(path, 'w') as output_file:
        for f in files:
            output_file.write('<a href=%s>%s</a><br />' % (f, f))



if __name__ == '__main__':
    # Handle arguments
    parser = argparse.ArgumentParser(description='RDF to HTML converter.')
    parser.add_argument('dcat_files', metavar='DCAT_FILE', type=str, nargs='+',
                        help='DCAT file')
    parser.add_argument('output', metavar='OUTPUT_DIR', type=str,
                        help='Output directory')
    parser.add_argument('--create-index', action='store_true',
                        help='Generate index.html with link to all files')

    args = parser.parse_args()

    for dcat_file in args.dcat_files:
        main(dcat_file, args.output)

    if args.create_index:
        gen_index(args.output)
