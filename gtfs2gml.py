#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Extract transport network graph from gtfs zip-file 

from collections import defaultdict
import logging
import logging.config
from itertools import izip
from gtfs_info import *
import networkx as nx
import optparse
import os
import sys
import transitfeed
from zipfile import is_zipfile

#setup logging
logging.config.fileConfig('logging.conf')

def options():
    usage  = 'usage: %prog [options] file'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--output_file', dest='output_file', type='string',
                      help='Output file name [default: "./%file%.gml"]', default=None)
    opts, files = parser.parse_args(sys.argv[1:])
    if len(files) < 1:
        logging.error('No files given %s.' %','.join(files))
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
        opts.output_file='%s.gml' %os.path.splitext(path)[0]
        logging.warning('No outputfile given (by option --output_file) using default output file "%s"' %opts.output_file)
    return opts, path

def read_config(config_file='%s_conf.yaml' %os.path.splitext(os.path.basename(__file__))[0]):
    with open(config_file, 'r') as f:
        return yaml.load(f)

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
    for x,y in pairwise(stops):
        try:
    	    weight = y.arrival_secs - x.departure_secs
        except TypeError:
            weight = None
        e_area=area[agency] if agency else ''
	label = {'weight': weight, 'route_type': route_type, 'agency': agency, 'area': e_area}
        G.add_edge(x.stop.stop_name, y.stop.stop_name, label)

def read_and_extract_graph(path,area):
    l=transitfeed.Loader(path)
    logging.warning('Reading feed "%s"' %path)
    feed = l.Load()
    logging.warning('Generating graph...')
    G = nx.DiGraph()
    for trip in feed.trips.itervalues():
        route_type = feed.routes[trip.route_id].route_type
        agency = feed.routes[trip.route_id].agency_id.strip('-_') if feed.routes[trip.route_id].agency_id else None
        add_stops2edges(G,trip.GetStopTimes(None), route_type, agency, area)
    return G
        
def write_gml(G,output_file='test.gml'):
    logging.warning('Writing gml file "%s"...' %output_file)
    nx.write_gml(G.to_undirected(), output_file)
    
if __name__ == '__main__':
    opts,path=options()
    gtfs_info_config=read_config(os.path.realpath('./gtfs_info_conf.yaml'))
    agencies_mapping=gtfs_info_config['agencies']['mappings']
    places=info(path,'agency.txt', lambda x,y: agencies(x,y,agencies_mapping))
    places={e[0]: e[2] for e in places[1]}
    G=read_and_extract_graph(path,places)
    write_gml(G,opts.output_file)
