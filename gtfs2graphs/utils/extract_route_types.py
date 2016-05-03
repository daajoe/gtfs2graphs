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
from collections import defaultdict
from graph import Graph
from helpers import read_config
import logging

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


def extract(G,M):
    d = defaultdict(Graph)
    #NOTE: we currently do not check whether a type is empty for combined types
    for v,w in G.edge_iter():
        route_type=G[(v,w)]['route_type']
        for key in M.iterkeys():
            if route_type in key:
                for t in M[key]:
                    d[t].add_edge(v,w,**G[(v,w)])
    return d


def extract_route_types(G):
    config = read_config(__file__)
    M = mapping(config['types'])
    return extract(G,M)

