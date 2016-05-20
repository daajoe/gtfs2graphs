#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2016
# Johannes K. Fichte, TU Wien, Austria
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

import collections
import csv
import json
import logging
import optparse
import os
import shutil
import signal
import socket
import tempfile
import time
import urllib
import urllib2
import urlparse
import zipfile
from StringIO import StringIO
from httplib import BadStatusLine
from itertools import izip

import eventlet
import sys
import yaml
from progressbar import Bar, Counter, ETA, FileTransferSpeed, Percentage, ProgressBar, RotatingMarker, Timer

from utils.helpers import read_config, chain_list, nested_get, setup_logging

setup_logging()
termsize = map(lambda x: int(x), os.popen('stty size', 'r').read().split())
config = read_config(__file__)

def options():
    print
    usage = 'usage: %prog [options] file'
    parser = optparse.OptionParser(usage=usage)
    group = optparse.OptionGroup(parser, 'Remark',
                        'Please put your API key into "%s/conf/get_feeds_conf.yaml" behind "key:" in quotes. '
                        'You can obtain an API key at "https://transitfeeds.com/api/keys"' %os.path.dirname(sys.argv[0]))
    parser.add_option_group(group)
    opts, files = parser.parse_args(sys.argv[1:])
    return opts, path


class Feed(object):
    @staticmethod
    def stream_iter(response):
        size = 64 * 1024
        while True:
            slice = response.read(size)
            if not slice: break
            yield slice

    @staticmethod
    def download_feed(feed_name, feed_url, stream_out, basename, timestamp='Sat, 29 Oct 1994 19:43:31 GMT', timeout=10,
                      user_agent='Mozilla/5.0 (Linux i686)'):
        # print('-'*termsize[1])
        eventlet.monkey_patch()
        with eventlet.Timeout(timeout):
            accepted = 'application/zip', 'application/x-zip-compressed'
            request = urllib2.Request(feed_url, headers={'User-agent': user_agent, #'Accept': ','.join(accepted),
                                                         'If-Modified-Since': timestamp})
            response = urllib2.urlopen(request)

        if response.info().get('content-type') not in accepted:
            logging.error('Wrong Content Type for url %s', feed_url)
            raise TypeError('Wrong Content Type for feed "%s" (url: "%s"). Expected type "%s" was %s' % (
            feed_name, feed_url, ','.join(accepted), response.info().get('content-type')))

        content_length = int(response.info().get('content-length'))
        last_modified = response.info().get('last-modified')

        if response.getcode() not in (200, 301, 302, 304):
            logging.error('HTTP error code %i', response.getcode())
            return

        if response.getcode() == 304:
            return

        # no content
        if content_length is None:
            logging.error('Empty File for url "%s"', feed_url)
            raise TypeError('Empty File for url %s' % feed_url)
        else:
            if type(feed_name) == unicode:
                feed_name = feed_name.encode('ascii', errors='ignore')
            logging.debug('(%s->%s):' % (feed_url, basename))
            feed_id = ','.join(urlparse.parse_qs(urlparse.urlparse(feed_url).query)['feed'])
            widgets = ['%s (%s->%s):' % ('', feed_id, basename), Percentage(), ' ', Bar(marker=RotatingMarker()),
                       ' ', ETA(), ' ', FileTransferSpeed()]
            pbar = ProgressBar(widgets=widgets, maxval=content_length).start()
            pbar.start()

            dl = 0
            for data in Feed.stream_iter(response):
                dl += len(data)
                pbar.update(dl)
                stream_out.write(data)
            stream_out.flush()
            pbar.finish()
        return last_modified


class TransitFeedAPI(object):
    def __init__(self, key, limit, feed_url, feed_download_url, user_agent='Mozilla/5.0 (Linux i686)', blacklist=None):
        self.__key = key
        self.__limit = limit
        self.__feed_url = feed_url
        self.__user_agent = user_agent
        self.__feed_download_url = feed_download_url
        self.__blacklist = blacklist

    def get_feeds_from_page(self, page=1):
        feed_args = {'key': self.__key, 'page': page, 'limit': self.__limit}
        url = '%s?%s' % (self.__feed_url, urllib.urlencode(feed_args))

        request = urllib2.Request(url, headers={'User-agent': self.__user_agent})
        try:
            response = urllib2.urlopen(request)
        except urllib2.URLError, e:
            logging.critical('Cannot connect to transit feed api. Error was "%s"' %e)
            exit(1)

        if response.getcode() != 200:
            logging.error('API query was unsucessful')
            return [], 0, 0
        try:
            feeds = json.loads(response.read())
            # with open('test_%i.json' % page, 'w') as f:
            #     json.dump(feeds, f)
        except ValueError, e:
            logging.error('API query was unsucessful. (url: %s, Error: %s)', url, e)
            raise ValueError('API query was unsucessful. (url: %s, Error: %s)' % (url, e))

        if feeds['status'] != 'OK':
            logging.error('Result from API was NOT ok.')
            raise RuntimeError('API query was unsucessful. Response %s' % feeds)

        if self.__limit != feeds['results']['limit']:
            logging.warning('Limits for transit feed url do not match (set limit = %i, returned limit = %i)',
                            self.__limit, feeds['results']['limit'])

        timestamp = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time()))
        return feeds['results']['feeds'], feeds['results']['page'], feeds['results']['numPages'], timestamp

    def get_all_feeds(self):
        try:
            results = list()
            results_json, _, num_pages, timestamp = self.get_feeds_from_page(page=1)
            results.extend(results_json)
            for i in xrange(2, num_pages + 1):
                results.extend(self.get_feeds_from_page(page=i)[0])
            results.sort()
            #filter by blacklist
            results = filter(lambda x: not any(e in x['t'] for e in self.__blacklist), results)
            return results, timestamp
        except urllib2.HTTPError, e:
            timestamp = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time()))
            if e.code == 401:
                logging.error('API key was probably wrong. Request returned %s', e)
                exit(1)
            else:
                logging.error('Request returned %s', e)
            return [], timestamp

    @staticmethod
    def _header_value_mappings(feed):
        d = collections.OrderedDict()
        d['api_id'] = ['id']
        d['name'] = ['t']
        d['url'] = ['u', 'd']
        d.update({e: ['l', e] for e in feed['l'].keys()})
        return d

    @staticmethod
    def _dataset(feed, m, timestamp, feed_url):
        ret = [nested_get(feed, v) for v in m.itervalues()]
        #fix download url to TransitFeed (not the data provider)
        ret[2]=feed_url %urllib.quote_plus(ret[0])
        ret.append(timestamp)
        return ret

    def _feeds2list(self):
        # download list of feeds from API
        logging.info('Downloading list of feeds from transitfeed API at %s', self.__feed_url)
        feeds, timestamp = self.get_all_feeds()
        mapping = self._header_value_mappings(feeds[0])
        # initialize with header
        ret = [mapping.keys() + ['downloaded']]
        # put feeds into list
        for feed in chain_list(feeds):
            ret.append(self._dataset(feed, mapping, timestamp, self.__feed_download_url))
        return ret

    def get_all_feeds_dict(self):
        L = self._feeds2list()
        return [{k: v for k, v in izip(L[0], e)} for e in L[1:]]

    @staticmethod
    def _feedlist2csv(L, stream=StringIO()):
        csvwriter = csv.writer(stream, delimiter=';')
        for line in L:
            # unicode encoding for commandline output
            line = map(lambda x: x.encode('utf8') if type(x) is unicode else x, line)
            csvwriter.writerow(line)
        return stream

    def get_all_feeds_as_csv(self, stream=StringIO()):
        L = self._feeds2list()
        return self._feedlist2csv(L, stream)
        

from utils.normalize_gtfs_archive import FeedArchive


class FeedList(object):
    def __init__(self, key, url, feed_download_url, path='./feeds', overwrite=False, datafile='./conf/data.yaml', timeout=10,
                 user_agent='Mozilla/5.0 (Linux i686)', blacklist=None):
        self.__api = TransitFeedAPI(key=key, limit=100, feed_url=url, feed_download_url=feed_download_url, blacklist=blacklist)
        self.__overwrite = overwrite
        path = os.path.realpath(path)
        if not os.path.exists(path):
            os.makedirs(path)
        self.__path = path
        self.__user_agent = user_agent
        self.__timeout = timeout
        self.__datafile = datafile
        if os.path.isfile(datafile):
            with open(datafile, 'r') as d:
                self.data = yaml.load(d)
        else:
            self.data = dict()
        self.__feed_download_url = feed_download_url

    def get_feeds(self):
        return self.__api.get_all_feeds_dict()

    def get_feeds_csv(self):
        return self.__api.get_all_feeds_as_csv().getvalue()

    def save_feed(self, feed_name, feed_url, filename, tmpfile, if_modified_since):
        feed_id = ','.join(urlparse.parse_qs(urlparse.urlparse(feed_url).query)['feed'])
        filename = filename.encode('ascii', errors='ignore')
        if not feed_url or feed_url == 'NA':
            logging.error('URL missing for feed "%s" (id "%s").', feed_name, feed_id)
            logging.info('Full url was "%s".', feed_url)
            return False, 'Missing url', None

        if not self.__overwrite and os.path.isfile(filename):
            logging.error('File "%s" does already exists. Skipping.', filename)
            return True, 'File exists.', None
        try:
            # download feed
            logging.debug('Saving download to tmpfile="%s"' %tmpfile)
            with open(tmpfile, 'wb') as stream_out:
                # timestamp=time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time()))
                try:
                    last_modified = Feed.download_feed(feed_name, feed_url, stream_out, os.path.basename(filename),
                                                       if_modified_since, self.__timeout, self.__user_agent)
                except TypeError, e:
                    logging.warning('No zip file for feed "%s" (id "%s") found.', feed_name, feed_id)
                    logging.info('Full url was "%s".', feed_url)
                    return False, 'NoZip', None
                except eventlet.timeout.Timeout, e:
                    logging.warning('Connection timeout error for feed "%s" (id "%s"). Error was: %s', feed_name,
                                    feed_url, e)
                    return False, 'Connection timeout', None
                except urllib2.URLError, e:
                    try:
                        if e.code == 304:
                            logging.warning('File "%s" for feed "%s" (id "%s") is up-to-date.',
                                            os.path.basename(filename), feed_name, feed_id)
                            logging.info('Full url was "%s".', feed_url)
                            return True, 'File "%s" for feed "%s" (url "%s") is up-to-date.' % (
                                filename, feed_name, feed_url), if_modified_since
                        if e.code == 500:
                            logging.warning('No file (e.g. only developer API) for feed "%s" (id "%s").',
                                            os.path.basename(filename), feed_id)
                            logging.info('Full url was "%s".', feed_url)
                            return False, 'No file "%s" for feed "%s" (url "%s").' %(
                                os.path.basename(filename), feed_name, feed_url), None
                    except AttributeError, e:
                        pass
                    logging.warning('Connection error for feed "%s" (id "%s"). Error was: %s', feed_name, feed_id, e)
                    logging.info('Full url was "%s".', feed_url)
                    return False, 'Connection error', None
                except (BadStatusLine,socket.error), e:
                    logging.warning('Connection error for feed "%s" (id "%s"). Unknown status code. Error was: %s', feed_name, feed_id, e)
                    logging.info('Full url was "%s".', feed_url)
                    return False, 'Connection error', None

                statinfo = os.stat(tmpfile)
                if statinfo.st_size == 0:
                    logging.warning('Empty file downloaded for feed "%s" (id "%s").', feed_name, feed_id)
                    logging.info('Full url was "%s".', feed_url)
                    return False, 'Empty file.', None

            logging.debug('Renaming tmpfile="%s" to "%s"' %(tmpfile,filename))
            shutil.move(tmpfile, filename)
            logging.debug('Renaming done.')
            # normalize feed
            arch = FeedArchive(filename)
            try:
                arch.normalize(replace=True)
            except zipfile.BadZipfile, e:
                logging.warning('Badzip for feed "%s" (id "%s") downloaded.', feed_name, feed_id)
                logging.info('Full url was "%s".', feed_url)
                return False, 'BadZip', last_modified
            except ValueError, e:
                logging.warning('Missing file in "%s" (id "%s"). Error Message was:', feed_name, feed_id, e)
                logging.info('Full url was "%s".', feed_url)
                return False, 'Missing file.', last_modified
            return True, 'OK', last_modified
        except KeyboardInterrupt, e:
            logging.warning('CTRL+C hit. Stopping download. Marking download as unsuccessful.')
            return False, 'User abort.', None

    def dump_yaml(self):
        with open(self.__datafile, 'w') as outfile:
            yaml.dump(self.data, outfile, allow_unicode=True)

    def save_all_feeds(self):
        f = self.get_feeds()
        widgets = ['Processed: ', Counter(), ' of %i feeds (' % len(f), Timer(), ')']
        pbar = ProgressBar(widgets=widgets, maxval=len(f) - 1)
        for feed in pbar(f[1:]):
            # check whether feed is in datafile
            d = self.data.get(feed['api_id'])
            if_modified_since = d.get('last_modified') if d and d.get('successful') else 'Thu, 01 Jan 1970 00:00:00 GMT'
            filename = '%s/%s.zip' % (
            self.__path, feed['name'].replace(' ', '_').replace('/', '-').encode('ascii', errors='ignore'))
            tmpfile=tempfile.mkstemp()[1]
            successful, msg, last_modified = self.save_feed(feed['name'], feed['url'], filename, tmpfile, if_modified_since)
            if os.path.exists(tmpfile):
                logging.info('Removing incomplete temporary file.')
                os.remove(tmpfile)
            self.data[feed['api_id']] = {'successful': successful, 'msg': msg, 'last_modified': last_modified,
                                         'filename': filename}
            self.dump_yaml()


def signal_handler(signum):
    logging.error('Signal %i received' % signum)
    logging.error('Writing progress to file')
    o.dump_yaml()
    logging.error('Exiting...')
    exit(1)


signal.signal(signal.SIGQUIT, signal_handler)


if __name__ == '__main__':
    opts, path = options()
    feed_download_url = config['get_feed_url']
    feed_download_url = feed_download_url.replace('%key',config['key'])
    o = FeedList(key=config['key'], url=config['feed_url'], feed_download_url=feed_download_url, path=config['feed_path'],
                 overwrite=True, timeout=config['timeout'], user_agent=config['user_agent'], blacklist=config['blacklist'])
    o.save_all_feeds()
