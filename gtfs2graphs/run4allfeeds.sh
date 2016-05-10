#!/usr/bin/env bash

shpath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

options=':hc:'
validate=""
while getopts $options option
do
    case $option in
	c)  validate="$OPTARG";;
        h)  error $EXIT $DRYRUN;;
	?)  printf "Usage: %s: [-c validate_path] path\n" $0
            exit 2;;
    esac
done

if [ -z "$validate" ]; then
    printf "No validation given.\n"
fi

shift $((OPTIND - 1))
path=$(realpath $1)

if [ ! -d "$path" ]; then
    printf "Directory does not exist. Exiting...\n"
    exit 2
fi

for file in $(find $path/*.zip -maxdepth 1 -type f) ; do 
    printf "Running gtfs2graphs for %s.\n" $file
    $shpath/gtfs2graphs.py $file
    if [ $? -ne 0 ] ; then
	printf "Error on %s.\n Exiting.\n" $file
	exit 2
    fi
    outputfile=$path/gr/$(basename $file)
    for gr_file in $(find $outputfile*.gr -maxdepth 1 -type f) ; do
	if [ -n "$validate" ]; then
	    printf "Validate %s... " $gr_file
	    $validate/td-validate $gr_file
	fi
    done;
done;
