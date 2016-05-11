# gtfs2graphs - A Transit Feed to Graph Format Converter #

* https://github.com/daajoe/gtfs2graphs

## Input ##

* gtfs format, see General Transit Feed Specification (GTFS) by Google
  [https://developers.google.com/transit/gtfs/] for details

## Output ##

* gr, see Appendix A: Graph format in Track A: Tree Width description
  of the PACE Challenge 2016
  [https://pacechallenge.wordpress.com/track-a-treewidth/]
* dimacs, see DIMACS Graph Format
  [http://prolland.free.fr/works/research/dsat/dimacs.html]
* gml, see Graph Modelling Language [https://en.wikipedia.org/wiki/Graph_Modelling_Language]
* lp, see e.g. Maximal Clique Problem Description
  [https://www.mat.unical.it/aspcomp2013/MaximalClique]


## System Requirements (gtfs2graphs.py) ##
### System ###
* python 2.7.9
* pip
* bash

### Python Packages ###

* transitfeed
* pyaml
* (networkx: only for gml output)

## System Requirements (get_feeds.py) ##
### System ###
* python 2.7.9
* pip
* bash
* python-dev

### Python Packages ###

* transitfeed
* pyaml
* (networkx: only for gml output)
* eventlet
* progressbar
