# RDF to HTML converter

A collection of scripts for generating human readable versions of DCAT XML
files.

## Setup
Run `python setup.py install`.

## Run
Run `rdf-to-html` for help.

## Develop
The generated files can of course be opened manually, but for convenience
a development web server is included at `devel/webserver.py`.

Just run `python webserver.py` in the folder where you have your
generated HTML-files and you can view them in your browser `localhost:8080/YOUR_FILE`.


## Automatically generate html
Run `./scripts/watch.sh FILES... OUTPUT_DIR` and the script will automatically
watch the specified files and generate an HTML file when a file is updated.
