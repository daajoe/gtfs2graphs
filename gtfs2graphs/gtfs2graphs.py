#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2016
# Johannes K. Fichte, Vienna University of Technology, Austria
#
# gtfs2graphs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.  gtfs2graphs is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public
# License along with gtfs2graphs.  If not, see
# <http://www.gnu.org/licenses/>.

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
from utils.extract_route_types import extract_route_types
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
                      help='Do not output symtab [default: %default]')
    parser.add_option('--no_labels', dest='labels', action='store_false', default=True,
                      help='Do not output labels [default: %default]')
    parser.add_option('--stdout', dest='stdout',  default=False,
                      help='Write output to stdout [default: %default]', action='store_true')
    parser.add_option('--no_split', dest='split',  default=True, action='store_false',
                      help='Do not provide additional transport type specific graphs (bus, metro, bus+metro,...). For route types configuration see: "conf/extract_route_types_conf.yaml". For route types see: "conf/route_types.csv" and "conf/route_types_extended.csv".')
    parser.add_option('--output_type', dest='output_type',  type='choice', choices=['gml','lp','dimacs'], 
                      help='Specifies the output type [default: %default]; allowed values: gml, lp, dimacs', default='dimacs')
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
        opts.output_file='%s.%s' %(os.path.splitext(path)[0],opts.output_type)
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


def save_graph(G,output_file,stdout,gtfs_filename,output_type,symtab,labels):
    if output_type == 'dimacs':
        from utils.graph_output import write_dimacs as write_graph
    elif output_type == 'lp':
        from utils.graph_output import write_lp as write_graph
    elif output_type == 'gml':
        from utils.graph_output import write_gml as write_graph
    else:
        logging.error('Output type (%s) not implemented' %opts.output_type)    

    output = cStringIO.StringIO()
    write_graph(G,symtab=symtab,labels=labels,output=output,gtfs_filename=gtfs_filename)
    
    if not stdout:
        logging.warning('Writing output to file')
        with open(output_file, 'w') as f:
            f.write(output.getvalue())
            f.flush()
        logging.warning('Output written to: %s' %output_file)
    else:
        print output.getvalue()


if __name__ == '__main__':
    opts,path=options()
    gtfs_info_config=read_config(filename='gtfs_info.py')
    agencies_mapping=gtfs_info_config['agencies']['mappings']
    places=info(path,'agency.txt', lambda x,y: agencies(x,y,agencies_mapping))
    places={e[0]: e[2] for e in places[1]}
    G=read_and_extract_graph(path,places)
    save_graph(G,output_file=opts.output_file,stdout=opts.stdout,gtfs_filename=os.path.basename(path),output_type=opts.output_type,symtab=opts.symtab,labels=opts.labels)
    
    D=extract_route_types(G)
    #TODO: NEXT
    for k,g in D.iteritems():
        print opts.output_file
        output_filename, output_file_extension = os.path.splitext(opts.output_file)
        output_filename = '%s_%s%s' %(output_filename, k, output_file_extension)
        filename=opts.output_file
        save_graph(g,output_file=output_filename,stdout=opts.stdout,gtfs_filename=os.path.basename(path),output_type=opts.output_type,symtab=opts.symtab,labels=opts.labels)
