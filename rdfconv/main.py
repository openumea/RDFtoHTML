"""
Main entry point
"""

import argparse
import logging
import sys
from rdfconv.converter import RDFtoHTMLConverter, LanguageError
import pyinotify


class EventHandler(pyinotify.ProcessEvent):
    """
    Class handling notifications when a watched file is changed
    """
    def __init__(self, output_folder, languages):
        super(EventHandler, self).__init__()
        self.output_folder = output_folder
        self.languages = languages

    def process_default(self, event):
        logging.info('%s changed', event.path)
        run(event.path, self.output_folder, self.languages)


def run(input_file, output_folder, languages='all'):
    """
    Run the RDF converter
    """
    try:
        logging.info('Converting %s', input_file)
        rdf_conv = RDFtoHTMLConverter(languages)
        rdf_conv.load_file(input_file)
        rdf_conv.output_html(output_folder)
        logging.info('Finished converting %s', input_file)
    except LanguageError as err:
        logging.error('Skipped file %s: %s', input_file, err)


def watch(input_files, output_folder, languages='all'):
    """
    Setup watching of given files
    """
    handler = EventHandler(output_folder, languages)
    watch_manager = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(watch_manager, handler)
    for input_file in input_files:
        watch_manager.add_watch(input_file, pyinotify.IN_MODIFY)
    notifier.loop()


def main():
    """
    Main entry point.
    Handle command line arguments and start the converter
    """
    # Handle arguments
    parser = argparse.ArgumentParser(
        description='RDF to HTML converter. Converts one or more RDF files '
                    'into a more human readable HTML representation.',)
    parser.add_argument('dcat_files', metavar='DCAT_FILE', type=str, nargs='+',
                        help='DCAT file(s)')
    parser.add_argument('output', metavar='OUTPUT_DIR', type=str,
                        help='Output directory')
    parser.add_argument('--languages', type=str, default='all',
                        help='Languages (on ISO-369-* format) to generate '
                             'separated by comma (,). If omitted all '
                             'encountered languages are generated.')
    parser.add_argument('--watch', action='store_true', help='Watch input '
                        'files for changes and run the conversion when a '
                        'change occurs.')
    parser.add_argument('--verbose', action='store_true',
                        help='Set log level to INFO instead of WARNING')
    parser.add_argument('--log-file', metavar='LOG_FILE',
                        help='File to log to. If omitted logging '
                             'will be sent to stdout')

    args = parser.parse_args()

    setup_logging(args.verbose, args.log_file)

    langs = args.languages.split(',')

    if args.watch:
        watch(args.dcat_files, args.output, langs)
    else:
        for dcat_file in args.dcat_files:
            run(dcat_file, args.output, langs)


def setup_logging(verbose, log_file):
    """
    Setup logging
    """

    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.WARN

    if log_file:
        stream = open(log_file, 'a')
    else:
        stream = sys.stdout

    logging.basicConfig(stream=stream, level=log_level,
                        format='%(asctime)s %(levelname)s '
                               '%(module)s %(message)s')


if __name__ == '__main__':
    main()
