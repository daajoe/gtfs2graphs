#!/usr/bin/env python
from collections import defaultdict
import logging
import networkx as nx
import optparse
import os
import sys
import yaml

def options():
    usage  = 'usage: %prog [options] file'
    parser = optparse.OptionParser(usage=usage)
    opts, files = parser.parse_args(sys.argv[1:])
    if len(files) < 1:
        logging.error('No files given %s.' %','.join(files))
        exit(1)
    if len(files) > 2:
        logging.error('Too many files given. Only one file expected.')
        exit(1)
    path = os.path.realpath(files[0])
    if not os.path.isfile(path):
        logging.error('File "%s" not found or not a file.', path)
        exit(1)
    return opts, path


def read_config(config_file='%s_conf.yaml' %os.path.splitext(os.path.basename(__file__))[0]):
    with open(config_file, 'r') as f:
        return yaml.load(f)

def extract_range(x):
    try:
        start,stop = map(lambda x: int(x), x.split('..'))
        x=(start,stop)
    except AttributeError:
        x=(x,x+1)
    return x

def mapping(L):
    ret = defaultdict(list)
    for k,v in L.iteritems():
        for i in v:
            ret[extract_range(i)].append(k)
    return {xrange(k[0],k[1]): v for k,v in ret.iteritems()}


def extract(path, M):
    d = defaultdict(nx.Graph)

    logging.info('Reading graph from %s', path)
    G = nx.read_gml(path)
    logging.info('Done reading graph')

    labels = dict()
    node_id=dict()
    for v, data in G.nodes_iter(data=True):
        labels[v]=data['label']
        node_id[data['label']]=v

    logging.info('Creating graphs ...')
    for v,w in G.edges_iter():
        route_type=G[v][w]['route_type']
        for key in M.iterkeys():
            if route_type in key:
                for t in M[key]:
                    d[t].add_edge(labels[v],labels[w],route_type=route_type, area=G[v][w]['area'], agency=G[v][w]['agency'],weight=G[v][w]['weight'])
    
    logging.info('Setting vertex attributes ...')
    for t in d.keys():
        for v in d[t].nodes_iter():
            d[t].node[v]['lat']=G.node[node_id[v]]['lat']
            d[t].node[v]['lon']=G.node[node_id[v]]['lon']
    logging.info('Done creating graphs')
    return d

def write_graphs(d,prefix):
    for k in d:
        path = '%s_subgraph_%s.gml' %(prefix, k)
        logging.warning('Writing graph %s to file %s' %(k, path))
        nx.write_gml(d[k], path)

if __name__ == '__main__':
    opts,path=options()
    output_name = os.path.splitext(os.path.basename(path))[0]
    output_dir = os.path.dirname(path)
    output_path_prefix = '%s/%s' %(output_dir, output_name)

    config=read_config()

    M=mapping(config['types'])
    d=extract(path,M)
    write_graphs(d,output_path_prefix)

