#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Graph(object):
    def __init__(self):
        self.__edges=set()
        self.__tab=dict()
        self.__node_label=dict()
        self.__edge_label=dict()

    def add_node(self,x, **label):
        v=self.__vertex_id(x)
        if label:
            self.__node_label[v]=label
        return v

    def add_edge(self,x,y,**label):
        v1,v2=self.__vertex_id(x),self.__vertex_id(y)
        self.__edges.add((v1,v2))
        if label:
            self.__edge_label[(v1,v2)]=label
        return (v1,v2)

    def __vertex_id(self,x):
        if self.__tab.has_key(x):
            return self.__tab[x]
        else:
            self.__tab[x]=len(self.__tab)+1
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

    def number_of_edges(self):
        return len(self.__edges)
