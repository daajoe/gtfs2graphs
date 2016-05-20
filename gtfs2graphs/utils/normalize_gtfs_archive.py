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

from contextlib import contextmanager
import glob
import logging
import shutil
import optparse
import os
import sys
import tempfile
from zipfile import is_zipfile, ZipFile, ZIP_DEFLATED


def options():
    usage = 'usage: %prog [options] file'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--output_file', dest='output_file', type='string',
                      help='Output file name [default: "./%file%.normalized.zip"]', default=None)
    opts, files = parser.parse_args(sys.argv[1:])
    if len(files) < 1:
        logging.error('No files given %s.' % ','.join(files))
        exit(1)
    if len(files) > 2:
        logging.error('Too many files given. Only one file expected.')
        exit(1)
    path = os.path.realpath(files[0])
    with open(path, 'rb') as fh:
        if not is_zipfile(fh):
            logging.error('File "%s" is not a zipfile.' % path)
            exit(1)
    if not opts.output_file:
        opts.output_file = '%s.normalized.zip' % os.path.splitext(path)[0]
        logging.warning(
            'No outputfile given (by option --output_file) using default output file "%s"' % opts.output_file)
    return opts, path


@contextmanager
def tempdir(directory='/dev/shm'):
    if not os.path.isdir(directory):
        logging.warning('(Default) temporary directory "%s" does not exist.' % directory)
        directory = None
        logging.warning('Setting directory to system default directory.')

    temp_folder = None
    try:
        temp_folder = tempfile.mkdtemp(dir=directory)
        yield temp_folder
    finally:
        shutil.rmtree(temp_folder)


class FeedArchive(object):
    def __init__(self, filename, output_filename=None):
        if not filename:
            logging.error('No filename given "%s"', filename)
            raise ValueError('No filename given "%s"' % filename)
        self.__filename = os.path.realpath(filename)
        if output_filename is None:
            output_filename = '%s.normalized.zip' % os.path.splitext(filename)[0]
        self.__output_filename = output_filename

    def find_file(self, txtfile='agency.txt'):
        with ZipFile(self.__filename) as z:
            filelist = z.namelist()
            if txtfile in filelist:
                logging.debug('File is "%s" is in place. File "%s" does not require normalization. Skipping...' % (
                txtfile, self.__filename))
                return './'
            folders = set([os.path.split(x)[0] for x in z.namelist() if '/' in x])
            for f in folders:
                if '%s/%s' % (f, txtfile) in filelist:
                    logging.info('Archive: %s Found file "%s" in subfolder "%s".', self.__filename, txtfile, f)
                    return f
            logging.error('No file named agency.txt found in zipfile "%s".' % self.__filename)
            raise ValueError('File "%s" is missing in "%s".' % (txtfile, self.__filename))

    def extract_and_recompress(self, folder):
        with tempdir() as tmp:
            with ZipFile(self.__filename) as z:
                z.extractall(tmp)
                files = glob.glob('%s/%s/*.txt' % (tmp, folder))
                with ZipFile(self.__output_filename, 'w', compression=ZIP_DEFLATED) as o:
                    for f in files:
                        o.write(f, os.path.basename(f))
                        logging.debug(f)

    def normalize(self, replace=False):
        folder = self.find_file()
        if folder != './':
            self.extract_and_recompress(folder)
            if replace:
                shutil.move(self.__output_filename, self.__filename)


if __name__ == '__main__':
    opts, path = options()
    arch = FeedArchive(filename=path, output_filename=opts.output_file)
    try:
        arch.normalize(replace=True)
    except ValueError, e:
        logging.error(e)
        exit(1)
