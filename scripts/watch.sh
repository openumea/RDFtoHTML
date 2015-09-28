#!/bin/bash

LOGFILE="rdf-to-html-log.txt"
touch $LOGFILE

# Watch for changes in given file and run the RDF-to-HTML conversion
# when a change occurs
set -e

if [ $# -lt 2 ]; then
  echo "Usage: watch FILES... OUTPUT_PATH"
fi

# Last argument is the output path
OUTPUT_PATH="${@: -1}"

# All other arguments are the files to watch
FILES=( "$@" )
unset "FILES[${#FILES[@]}-1]" 

# Keep track of filenames for all the files
TIMESTAMPS=()
for i in "${!FILES[@]}"; do
  TIMESTAMPS[$i]=`stat -c %Z "${FILES[$i]}"`
done

# Watch for changes until we quite the script
while true; do
  for i in "${!FILES[@]}"; do
    ATIME=`stat -c %Z "${FILES[$i]}"`
    if [[ "$ATIME" != "${TIMESTAMPS[$i]}" ]]
    then
      echo "${FILES[$i]}" has changed, running html converter >> $LOGFILE
      python main.py "${FILES[$i]}" $OUTPUT_PATH >> $LOGFILE
      TIMESTAMPS[$i]=$ATIME
    fi
  done
  sleep 5
done
