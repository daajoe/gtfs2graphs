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

import logging
import operator


# TODO: agency mapping and splitting

def quote(x):
    if isinstance(x, int):
        return str(x)
    else:
        return '"%s"' % x


def write_lp(G, output, symtab=True, labels=True, gtfs_filename=''):
    def comment(x):
        return '% ' + '%s' % x

    num_edges = G.number_of_edges()

    output.write(comment('original_input_file: %s\n' % gtfs_filename))
    if symtab:
        output.write(comment('%s \n' % ('-' * 80)))
        output.write(comment('Symbol Table\n'))
        for val, num_id in sorted(G.get_symtab().items(), key=operator.itemgetter(1)):
            output.write('tab(%s,"%s").\n' % (num_id, val))
    if labels:
        output.write(comment('%s \n' % ('-' * 80)))
        output.write(comment('Edge Labels\n'))
        first = True
        for edge, val in sorted(G.get_edge_labels().items(), key=operator.itemgetter(0)):
            if first:
                output.write(comment('edge_label(id,id,%s).\n' % (','.join(map(quote, val.keys())))))
                first = False
            output.write('edge_label(%i,%i,%s).\n' % (edge[0], edge[1], ','.join(map(quote, val.values()))))

        output.write(comment('%s \n' % ('-' * 80)))
        output.write(comment('Vertex Labels\n'))
        first = True
        for vertex_id, val in sorted(G.get_node_labels().items(), key=operator.itemgetter(0)):
            if first:
                output.write(comment('vertex_label(id,%s).\n' % ','.join(map(quote, val.keys()))))
                first = False
            output.write('vertex_label(%i,%s).\n' % (vertex_id, ','.join(map(quote, val.values()))))

        output.write(comment('%s \n' % ('-' * 80)))

    for x, y in G:
        output.write('edge(%s,%s).\n' % (x, y))
    output.flush()
    return output


def write_gml(G, output, symtab=True, labels=True, gtfs_filename=''):
    try:
        import networkx as nx
    except ImportError, e:
        logging.error('Package missing %e')
        logging.error('Try "pip install networkx"')

    GML = nx.DiGraph()

    for x, y in G:
        GML.add_edge(x, y)

    if symtab:
        for val, num_id in sorted(G.get_symtab().items(), key=operator.itemgetter(1)):
            GML.node[num_id]['label'] = val
            GML.node[num_id]['gen_id'] = num_id

    if labels:
        for edge, val in sorted(G.get_edge_labels().items(), key=operator.itemgetter(0)):
            for k, v in val.iteritems():
                GML.edge[edge[0]][edge[1]][k] = v

        for vertex_id, val in sorted(G.get_node_labels().items(), key=operator.itemgetter(0)):
            for k, v in val.iteritems():
                GML.node[vertex_id][k] = v
    nx.write_gml(GML.to_undirected(), output)
    return output


def write_dimacs_like(G, output, symtab=True, labels=True, gtfs_filename='', descriptor='', edge_char='e '):
    output.write('c Contains a public transit graph extracted from GTFS file\n')
    output.write('c original_input_file: %s\n' % gtfs_filename)
    if symtab:
        output.write('c %s \n' % ('-' * 40))
        output.write('c Symbol Table\n')
        for val, num_id in sorted(G.get_symtab().items(), key=operator.itemgetter(1)):
            output.write('c tab %s | %s\n' % (num_id, val))

    if labels:
        output.write('c %s \n' % ('-' * 40))
        output.write('c Edge Labels\n')
        for edge, val in sorted(G.get_edge_labels().items(), key=operator.itemgetter(0)):
            output.write('c edge %s | %s\n' % (edge, val))

        output.write('c %s \n' % ('-' * 40))
        output.flush()
        
        output.write('c Vertex Labels\n')
        for vertex_id, val in sorted(G.get_node_labels().items(), key=operator.itemgetter(0)):
            output.write('c node %s | %s\n' % (vertex_id, val))
        output.flush()
        output.write('c %s \n' % ('-' * 40))

    output.write('p %s %i %i\n' % (descriptor, G.num_edges(), G.num_vertices()))
    for x, y in G:
        output.write('%s%s %s\n' % (edge_char,x, y))
    output.flush()
    return output

def write_dimacs(G, output, symtab=True, labels=True, gtfs_filename=''):
    return write_dimacs_like(G, output, symtab=True, labels=True, gtfs_filename='', descriptor='edge', edge_char='e ')

def write_gr(G, output, symtab=True, labels=True, gtfs_filename=''):
    return write_dimacs_like(G, output, symtab=True, labels=True, gtfs_filename='', descriptor='tw', edge_char='')
