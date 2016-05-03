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
import operator

def write_gml(G,output='test.gml',gtfs_filename=''):
    import networkx as nx
    logging.warning('Writing gml file "%s"...' %output_file)

    GML = nx.DiGraph()
    #G = nx.DiGraph()
    #for trip in feed.trips.itervalues():
    #    route_type = feed.routes[trip.route_id].route_type
    #    agency = feed.routes[trip.route_id].agency_id.strip('-_') if feed.routes[trip.route_id].agency_id else None
    #    add_stops2edges(G,trip.GetStopTimes(None), route_type, agency, area)

    nx.write_gml(GML.to_undirected(), output_file)



def write_dimacs(G,output,symtab=True,labels=True,gtfs_filename=''):
    output.write('c original_input_file:%s\n' %gtfs_filename)
    if symtab:
        output.write('c %s \n' %('-'*40))
        output.write('c Symbol Table\n')
        for val,num_id in sorted(G.get_symtab().items(), key=operator.itemgetter(1)):
            output.write('c tab %s:::%s\n' %(num_id,val))

    if labels:
        output.write('c %s \n' %('-'*40))
        output.write('c Edge Labels\n')
        for edge,val in sorted(G.get_edge_labels().items(), key=operator.itemgetter(1)):
            output.write('c edge %s:::%s\n' %(edge,val))

        output.write('c %s \n' %('-'*40))
        output.write('c Vertex Labels\n')
        for vertex_id,val in sorted(G.get_node_labels().items(), key=operator.itemgetter(1)):
            output.write('c node %s:::%s\n' %(vertex_id,val))
        output.write('c %s \n' %('-'*40))

    output.write('p edges %i %i\n' %(G.num_edges(),G.num_vertices()))
    for x,y in G:
        output.write('e %s %s\n' %(x,y))
    output.flush()
