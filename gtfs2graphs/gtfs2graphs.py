#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Extract transport network graph from gtfs zip-file 

from collections import defaultdict
import cStringIO
import logging
import logging.config
from itertools import izip
import optparse
import os
import sys
import transitfeed
from utils.gtfs_info import *
from utils.helpers import setup_logging, read_config
from utils.graph import Graph
from zipfile import is_zipfile

setup_logging()

def options():
    usage  = 'usage: %prog [options] file'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--output_file', dest='output_file', type='string',
                      help='Output file name [default: "./%file%.%type%"]', default=None)
    parser.add_option('--no_symtab', dest='symtab', action='store_false', default=True,
                      help='Do not output symtab [default: False]')
    parser.add_option('--no_labels', dest='labels', action='store_false', default=True,
                      help='Do not output labels [default: False]')
    parser.add_option('--stdout', dest='stdout',  default=False,
                      help='Write output to stdout [default: False]', action='store_true')

    opts, files = parser.parse_args(sys.argv[1:])
    if len(files) < 1:
        logging.error('No files given %s.' %','.join(files))
        print '*'*80
        parser.print_help()
        exit(1)
    if len(files) > 2:
        logging.error('Too many files given. Only one file expected.')
        exit(1)
    path = os.path.realpath(files[0])
    with open(path, 'rb') as fh:
        if not is_zipfile(fh):
            logging.error('File "%s" is not a zipfile.' %path)
            exit(1)
    if not opts.output_file:
        opts.output_file='%s.dimacs' %os.path.splitext(path)[0]
        logging.warning('No outputfile given (by option --output_file) using default output file "%s"' %opts.output_file)
    return opts, path

def pairwise(t):
    if t == []:
        return []
    it = iter(t)
    it2 = iter(t)
    it2.next()
    return izip(it,it2)

def add_stops2edges(G,stops, route_type, agency, area):
    for x in stops:
    	G.add_node(x.stop.stop_name, lat=x.stop.stop_lat, lon=x.stop.stop_lon)
    #utf-8 decoding
    area={k.decode('utf-8'):v.decode('utf-8') for k,v in area.iteritems()}

    for x,y in pairwise(stops):
        try:
    	    weight = y.arrival_secs - x.departure_secs
        except TypeError:
            weight = None
        e_area=area[agency] if agency else ''
        G.add_edge(x.stop.stop_name, y.stop.stop_name, weight=weight, route_type=route_type, agency=agency, area=e_area)

def read_and_extract_graph(path,area):
    l=transitfeed.Loader(path)
    logging.warning('Reading feed "%s"' %path)
    feed = l.Load()
    logging.warning('Generating graph...')
    G = Graph()
    for trip in feed.trips.itervalues():
        route_type = feed.routes[trip.route_id].route_type
        agency = feed.routes[trip.route_id].agency_id.strip('-_') if feed.routes[trip.route_id].agency_id else None
        add_stops2edges(G,trip.GetStopTimes(None), route_type, agency, area)
    return G
    
if __name__ == '__main__':
    opts,path=options()
    gtfs_info_config=read_config(filename='gtfs_info.py')
    agencies_mapping=gtfs_info_config['agencies']['mappings']
    places=info(path,'agency.txt', lambda x,y: agencies(x,y,agencies_mapping))
    places={e[0]: e[2] for e in places[1]}
    G=read_and_extract_graph(path,places)
    from utils.graph_output import write_dimacs as write_graph
    output = cStringIO.StringIO()
    write_graph(G,symtab=opts.symtab,labels=opts.labels,output=output,gtfs_filename=os.path.basename(path))
    
    if not opts.stdout:
        logging.warning('Writing output to file')
        with open(opts.output_file, 'w') as f:
            f.write(output.getvalue())
            f.flush()
        logging.warning('Output written to: %s' %opts.output_file)
    else:
        print output.getvalue()
