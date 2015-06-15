import sys
import logging
from rdfconv.rdfconv import RDFtoHTMLConverter

# rdflib requires a logger to be setup
logging.basicConfig()

def main(input_file, output_folder):
    """
    Run the RDF converter
    """
    rdf_conv = RDFtoHTMLConverter()
    rdf_conv.load_file(input_file)
    rdf_conv.output_html(output_folder)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: main.py DCAT_INPUT_FILE OUTPUT_FOLDER'
        sys.exit(0)
    main(sys.argv[1], sys.argv[2])
