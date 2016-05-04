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

class Graph(object):
    def __init__(self):
        self.__edges = set()
        self.__tab = dict()
        self.__id_tab = dict()
        self.__node_label = dict()
        self.__edge_label = dict()

    def add_node(self, x, **label):
        v = self.__vertex_id(x)
        if label:
            self.__node_label[v] = label
        return v

    def add_edge(self, x, y, **label):
        v1, v2 = self.__vertex_id(x), self.__vertex_id(y)
        self.__edges.add((v1, v2))
        if label:
            self.__edge_label[(v1, v2)] = label
        return (v1, v2)

    def __vertex_id(self, x):
        if self.__tab.has_key(x):
            return self.__tab[x]
        else:
            self.__tab[x] = len(self.__tab) + 1
            self.__id_tab[self.__tab[x]] = x
            return self.__tab[x]

    def edge_iter(self):
        return iter(self.__edges)

    def __iter__(self):
        return self.edge_iter()

    def num_edges(self):
        return len(self.__edges)

    def num_vertices(self):
        return len(self.__tab)

    def get_symtab(self):
        return self.__tab

    def get_edge_labels(self):
        return self.__edge_label

    def get_node_labels(self):
        return self.__node_label

    def get_node_name(self, x):
        return self.__id_tab[x]

    def number_of_edges(self):
        return len(self.__edges)

    def __getitem__(self, x):
        if isinstance(x, tuple):
            return self.get_edge_labels()[x]
        else:
            return self.get_node_labels()[x]
