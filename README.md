# RDF to HTML converter

The RDF to HTML converter aim to provide documentation for RDF files by generating
a more human readable version of the data.

The converter currently supports splitting all subjects of an RDF file into separate paragraphs,
each with a title, type and description. Each paragraph can then be expanded to show all data
contained in the file.

To further improve the readability, the converter also tries to download the specification
for all predicates in the file. This allows it to generate a more human version of the predicates
as well.

The HTML files output by the converter will be html files with a language suffix (.en, .sv, etc.)
to allow tools such as Apache mod_negotiation to serve different languages based on the users
preferences.

## Setup
* Create a virtual environment and activate it `virtualenv venv; . venv/bin/activate`
* Run `python setup.py install` you will now have an executable named `rdf-to-html` in your path

## Run
```
usage: rdf-to-html [-h] [--languages LANGUAGES] [--watch] [--verbose]
                   [--log-file LOG_FILE]
                   DCAT_FILE [DCAT_FILE ...] OUTPUT_DIR

RDF to HTML converter.

positional arguments:
  DCAT_FILE             DCAT file
  OUTPUT_DIR            Output directory

optional arguments:
  -h, --help            show this help message and exit
  --languages LANGUAGES
                        Languages (on ISO-369-* format) to generate separated
                        by comma (,). If omitted all encountered languages are
                        generated.
  --watch               Watch input files for changes and run the conversion
                        when a change occurs.
  --verbose             Only log critical events
  --log-file LOG_FILE   File to log to. If omitted logging will be sent to
                        stdout

```
### Examples
The typical use case is to setup the script to watch for changes in one or more RDF files.
This will enable you to always have an up to date human readable version of your datafile.
To to this setup the following code to be run when the server starts `rdf-to-html --watch DCAT_FILE [DCAT_FILE ...] OUTPUT_DIR`.
The conversion script will then run everytime the files change.


## Develop
The generated files can of course be opened manually, but for convenience
a development web server is included at `devel/webserver.py`.

Just run `python webserver.py` in the folder where you have your
generated HTML-files and you can view them in your browser `localhost:8080/YOUR_FILE`.

