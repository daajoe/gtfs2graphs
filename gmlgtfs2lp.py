#!/usr/bin/env python
from itertools import imap, izip
import contextlib
import logging
import networkx as nx
import optparse
import os
import sys

def options():
    usage  = 'usage: %prog [options] file'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-i", "--integer_only", dest="ints_only", help="Output file", action='store_true', default=False)
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


def rm_dup_whs(x):
    return ' '.join(x.split())


def gml2lp(stream,filename,int_only=False):
    G=nx.read_gml(filename)
    num_edges=G.number_of_edges()

    stream.write('%vertex(name,lat,lon).\n')
    labels = dict()
    for v, data in G.nodes_iter(data=True):
        labels[v]=data['label']
        stream.write('vertex("%s",%s,%s).\n' %(rm_dup_whs(data['label'].encode('utf8')), data['lat'], data['lon']))

    stream.write('%' + 'extracted from %s\n' %filename)
    stream.write('%edge(v,w,type,agency,weight)\n')
    for v,w in G.edges_iter():
        if int_only:
            stream.write('edge(%i,%i).\n' % (v, w))
        else:
            try:
                x='edge("%s","%s",%s,"%s",%s).\n' %(rm_dup_whs(labels[v]), rm_dup_whs(labels[w]),G[v][w]['route_type'],G[v][w]['agency'],G[v][w]['weight'])
                stream.write(x.encode('utf8'))
            except KeyError:
                pass
            x = 'edge("%s","%s").\n' % (rm_dup_whs(labels[v]), rm_dup_whs(labels[w]))
            stream.write(x.encode('utf8'))


if __name__ == '__main__':
    opts,path=options()
    gml2lp(sys.stdout,path,opts.ints_only)
