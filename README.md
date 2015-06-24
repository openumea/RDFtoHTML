#RDF to HTML converter

A collection of scripts for generating human readable versions of DCAT XML
files.

Setup
-----
1. Install requirements `pip install -r requirements.txt`

Run
---
Run the script `python main.py DCAT_INPUT_FILE OUTPUT_FOLDER`.
It will store all output HTML in the given folder.
The script will generate one file per language per resource.
To link all files together summary files are created for each language.
The summary file will be named as the input file.
