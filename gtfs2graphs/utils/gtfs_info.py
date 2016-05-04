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

# Extract information about agencies and route types from gtfs zip-file

import StringIO
import csv
import logging
import logging.config
import operator
import optparse
import os
import shutil
import sys
import tempfile
import urllib2
from contextlib import contextmanager
from itertools import ifilter
from zipfile import ZipFile, is_zipfile

from helpers import setup_logging, read_config

setup_logging()


def options():
    usage = 'usage: %prog [options] [files]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--agencies', dest='agencies',
                      action='store_true', help='Show available transport agencies', default=False)
    parser.add_option('--route_types', dest='route_types',
                      action='store_true', help="Show used route types", default=False)
    opts, files = parser.parse_args(sys.argv[1:])
    return opts, files


def read_area_codes(tmp_file, url):
    res = {}
    # download area code file
    if not os.path.isfile(tmp_file):
        response = urllib2.urlopen(url)
        html = response.read()
        with open(tmp_file, 'w+') as f:
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
def zopen(path, filename):
    if os.path.isdir(path):
        try:
            fh = open('%s/%s' % (path, filename), 'rb')
            yield fh
        finally:
            fh.close()
    else:
        try:
            fh = open(path, 'rb')
            if is_zipfile(fh):
                z = ZipFile(fh)
                yield z.read(filename)
            else:
                raise IOError('Unknown file type for file %s.' % path)
        finally:
            fh.close()


def read_routes(path='route_types_extended.csv'):
    with open(path, 'rb') as csv_route_types:
        reader = csv.reader(csv_route_types, delimiter=',')
        header = reader.next()
        route_types = {int(row[0]): row[1] for row in reader}
    return route_types


def read_all_routes(L):
    res = {}
    for path in L:
        res.update(read_routes(os.path.realpath(path)))
    return res


def sorted_dict(d, s):
    return sorted(d, key=operator.itemgetter(s))


def route_types(header, reader, types):
    routes = set()
    i = header.index('route_type')
    for row in reader:
        routes.add(int(row[i]))
    return ('route', 'type'), sorted_dict([[e, types[e] if types.has_key(e) else 'Unbekannt'] for e in routes], 1)


def areacode2city(x, name, area_codes, default_mapping):
    if default_mapping.has_key(x):
        return default_mapping[x]
    area = x.split(' ')[0]
    if area_codes.has_key(area):
        return area_codes[area]
    logging.warning('Unknown area code for %s (%s)' % (x, name))
    return x


def agencyid2city(x, name, phone, default_mapping):
    x = x.strip('-_')
    if default_mapping.has_key(x):
        return default_mapping[x]
    # logging.warning('Unknown area code for %s (%s) phone:%s' %(x, name, phone))
    return x


def indexOrNone(L, value):
    try:
        return L.index(value)
    except ValueError:
        return None


def agencies(header, reader, default_mapping):
    # strip whitespaces
    header = map(lambda x: x.strip(), header)
    phone = indexOrNone(header, 'agency_phone')
    agency_id = indexOrNone(header, 'agency_id')
    agency_name = indexOrNone(header, 'agency_name')
    if agency_id is None:
        agency_id = agency_name
    res = []
    for row in reader:
        # skip empty lines
        if row == []:
            continue
        city = agencyid2city(row[agency_id], row[agency_name], row[phone] if phone else None, default_mapping)
        res.append([row[agency_id].strip('-_'), row[agency_name].decode('utf8'), city])
    return ('agency_id', 'agency_name', 'place'), sorted_dict(res, 2)


def info(path, filename, func):
    with zopen(path, filename) as fh:
        reader = csv.reader(StringIO.StringIO(fh), delimiter=',')
        header = reader.next()
        # remove bom if necessary
        header[0] = header[0][3:] if header[0].decode('utf8').startswith(u'\ufeff') else header[0]
        res = func(header, reader)
    return res


def csv2stdout(d):
    writer = csv.writer(sys.stdout, delimiter=',')
    writer.writerow(d[0])
    for e in d[1]:
        row = [unicode(i).encode('utf8') for i in e]
        writer.writerow(row)


if __name__ == '__main__':
    opts, files = options()
    config = read_config()
    types = read_all_routes(config['types'].values())
    # area_codes=read_area_codes(config['area_codes']['tmp_file'], config['area_codes']['url'])
    # area_codes_mapping=config['area_codes']['mappings']
    agencies_mapping = config['agencies']['mappings']
    for f in files:
        if not os.path.isfile(f):
            raise IOError('File %s not found.' % f)
        if opts.agencies:
            csv2stdout(info(f, 'agency.txt', lambda x, y: agencies(x, y, agencies_mapping)))
        if opts.route_types:
            csv2stdout(info(f, 'routes.txt', lambda x, y: route_types(x, y, types)))
    exit(0)
