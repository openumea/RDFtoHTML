"""
Main entry point
"""

import argparse
from rdfconv.loader import RDFtoHTMLConverter, LanguageError


def run(input_file, output_folder, languages='all'):
    """
    Run the RDF converter
    """
    rdf_conv = RDFtoHTMLConverter(languages)
    rdf_conv.load_file(input_file)
    rdf_conv.output_html(output_folder)


def main():
    # Handle arguments
    parser = argparse.ArgumentParser(description='RDF to HTML converter.')
    parser.add_argument('dcat_files', metavar='DCAT_FILE', type=str, nargs='+',
                        help='DCAT file')
    parser.add_argument('output', metavar='OUTPUT_DIR', type=str,
                        help='Output directory')
    parser.add_argument('--languages', type=str, default='all',
                        help='Languages to generate separated by comma (,). '
                             'If omitted all encountered languages are '
                             'generated.')

    args = parser.parse_args()

    langs = args.languages.split(',')

    for dcat_file in args.dcat_files:
        try:
            run(dcat_file, args.output, langs)
        except LanguageError as err:
            print 'Skipped file %s due to error:\n%s' % (dcat_file, err)


if __name__ == '__main__':
    main()
