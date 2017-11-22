# gtfs2graphs - A Transit Feed to Graph Format Converter #

* https://github.com/daajoe/gtfs2graphs
* [Brief Documentation (PDF)](https://github.com/daajoe/transit_graphs/blob/master/transitfeeds-tw.pdf)

## Input ##

* gtfs format, see [General Transit Feed Specification (GTFS) by Google]
  (https://developers.google.com/transit/gtfs/) for details

## Output ##

* gr, see Appendix A: Graph format in Track A: Tree Width description
  of the [PACE Challenge 2016]
  (https://pacechallenge.wordpress.com/track-a-treewidth/)
* dimacs, see [DIMACS Graph Format]
  (http://prolland.free.fr/works/research/dsat/dimacs.html)
* gml, see [Graph Modelling Language] (https://en.wikipedia.org/wiki/Graph_Modelling_Language)
* lp, see e.g. [Maximal Clique Problem Description]
  (https://www.mat.unical.it/aspcomp2013/MaximalClique)


## System Requirements (gtfs2graphs.py) ##
### System ###
* python 2.7.9
* pip
* bash

### Python Packages ###

* transitfeed
* (pytz: to avoid warnings of transitfeed)
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

## References / Links ##
* [Extended GTFS Route Types] (https://support.google.com/transitpartners/answer/3520902?hl=en)
* [Google Transit Extensions to GTFS] (https://support.google.com/transitpartners/answer/2450962?hl=en)
* [General Transit Feed Specification Reference] (https://developers.google.com/transit/gtfs/reference?hl=en#routes_fields)
* [What is GTFS?] (https://developers.google.com/transit/gtfs/?hl=en)
* [googletransitdatafeed] (https://code.google.com/p/googletransitdatafeed/wiki/PublicFeeds)
* [Transit Agencies Providing GTFS Data] (http://www.gtfs-data-exchange.com/agencies/bylocation#filter_official)
* [Transit Feeds API] (https://transitfeeds.com)
