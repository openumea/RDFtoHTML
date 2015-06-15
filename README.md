#RDF to HTML converter

A collection of scripts for generating human readable versions of DCAT XML
files.

Setup
-----
1. Install requirements `pip install -r requirements.txt`

Run
---
Run the script `python main.py DCAT_INPUT_FILE OUTPUT_FOLDER`.
It will store all output HTML in the given folder. A separate sub-folder will be
created for each language encountered in DCAT input file. Each resource
encountered in the DCAT input file will be output to a separate file.

To link all files together index.html files are created for each language
together with a top level index file pointing to each language.
