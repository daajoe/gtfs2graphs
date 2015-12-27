#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Extract information about agencies and route types from gtfs zip-file 

from collections import defaultdict
from contextlib import contextmanager
import csv
from itertools import ifilter
import logging
import logging.config
import re
import operator
import optparse
import os
import shutil
import sys
import StringIO
import tempfile
import urllib2
import yaml
from zipfile import ZipFile, is_zipfile

#setup logging
logging.config.fileConfig('logging.conf')

def options():
    usage  = 'usage: %prog [options] [files]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--agencies', dest='agencies',
                      action='store_true', help='Show available transport agencies', default=False)
    parser.add_option('--route_types', dest='route_types',
                      action='store_true', help="Show used route types", default=False)
    opts, files = parser.parse_args(sys.argv[1:])
    return opts, files

def read_config(config_file='%s_conf.yaml' %os.path.splitext(os.path.basename(__file__))[0]):
    with open(config_file, 'r') as f:
        return yaml.load(f)


def read_area_codes(tmp_file,url):
    res = {}
    #download area code file
    if not os.path.isfile(tmp_file):
        response = urllib2.urlopen(url)
        html = response.read()
        with open(tmp_file,'w+') as f:
            f.write(html)
            f.flush()
    with open(tmp_file, 'rb') as f:
        reader = csv.reader(ifilter(None, (line.rstrip() for line in f)), delimiter=';')
        header = reader.next()
        return {row[3]: row[0] for row in reader}
    
@contextmanager
def tempfolder():
    try:
	path = tempfile.mkdtemp()
	yield path
    finally:
	shutil.rmtree(path)	

@contextmanager
def zopen(path,filename):
    if os.path.isdir(path):
        try:
            fh=open('%s/%s' %(path, filename), 'rb')
            yield fh
        finally:
            fh.close()
    else:
        try:
            fh=open(path, 'rb')
            if is_zipfile(fh):
                z = ZipFile(fh)
                yield z.read(filename)
            else:
                raise IOError('Unknown file type for file %s.' %path)
        finally:
            fh.close()
        
def read_routes(path='route_types_extended.csv'):
    with open(path, 'rb') as csv_route_types:
        reader = csv.reader(csv_route_types, delimiter=',')
        header = reader.next()
        route_types={int(row[0]): row[1] for row in reader}
    return route_types

def read_all_routes(L):
    res={}
    for path in L:
        res.update(read_routes(os.path.realpath(path)))
    return res

def sorted_dict(d,s):
    return sorted(d, key=operator.itemgetter(s))

def route_types(header,reader,types):
    routes = set()
    i=header.index('route_type')
    for row in reader:
        routes.add(int(row[i]))
    return ('route','type'), sorted_dict([[e, types[e] if types.has_key(e) else 'Unbekannt'] for e in routes],1)

def areacode2city(x, name, area_codes, default_mapping):
    if default_mapping.has_key(x):
        return default_mapping[x]
    area=x.split(' ')[0]
    if area_codes.has_key(area):
        return area_codes[area]
    logging.warning('Unknown area code for %s (%s)' %(x, name))
    return x

def agencyid2city(x, name, phone, default_mapping):
    x=x.strip('-_')
    if default_mapping.has_key(x):
        return default_mapping[x]
    #logging.warning('Unknown area code for %s (%s) phone:%s' %(x, name, phone))
    return x
    
def agencies(header,reader,default_mapping):
    #areacode2city(row[5], row[1], area_codes, default_mapping)
    return ('short_name', 'long_name','place'), sorted_dict([[row[0].strip('-_'), row[1].decode('utf8'),agencyid2city(row[0], row[1], row[5] if len(row)>4 else None, default_mapping)] for row in reader],2)

def info(path,filename, func):
    with zopen(path, filename) as fh:
        reader = csv.reader(StringIO.StringIO(fh), delimiter=',')
        header = reader.next()
        res=func(header,reader)
    return res

def csv2stdout(d):
    writer = csv.writer(sys.stdout, delimiter=',')
    writer.writerow(d[0])
    for e in d[1]:
        row = [unicode(i).encode('utf8') for i in e]
        writer.writerow(row)

if __name__ == '__main__':
    opts,files=options()
    config=read_config()
    types = read_all_routes(config['types'].values())
    #area_codes=read_area_codes(config['area_codes']['tmp_file'], config['area_codes']['url'])
    #area_codes_mapping=config['area_codes']['mappings']
    agencies_mapping=config['agencies']['mappings']
    for f in files:
        if not os.path.isfile(f):
            raise IOError('File %s not found.' %f)
        if opts.agencies:
            csv2stdout(info(f,'agency.txt', lambda x,y: agencies(x,y,agencies_mapping)))
        if opts.route_types:
            csv2stdout(info(f,'routes.txt', lambda x,y: route_types(x,y,types)))
    exit(0)



