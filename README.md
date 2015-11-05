# RDF to HTML converter

A collection of scripts for generating human readable versions of DCAT XML
files.

## Setup
Install requirements `pip install -r requirements.txt`

## Run
Run `python main.py -h` for help

## Automatically generate html
Run `./scripts/watch.sh FILES... OUTPUT_DIR` and the script will automatically
watch the specified files and generate an HTML file when a file is updated.
