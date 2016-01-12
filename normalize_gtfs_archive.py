#!/usr/bin/env python
from contextlib import contextmanager
import glob
import logging
import shutil
import optparse
import os
import sys
import tempfile
from zipfile import is_zipfile, ZipFile

def options():
    usage  = 'usage: %prog [options] file'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--output_file', dest='output_file', type='string',
                      help='Output file name [default: "./%file%.normalized.zip"]', default=None)
    opts, files = parser.parse_args(sys.argv[1:])
    if len(files) < 1:
        logging.error('No files given %s.' %','.join(files))
        exit(1)
    if len(files) > 2:
        logging.error('Too many files given. Only one file expected.')
        exit(1)
    path = os.path.realpath(files[0])
    with open(path, 'rb') as fh:
        if not is_zipfile(fh):
            logging.error('File "%s" is not a zipfile.' %path)
            exit(1)
    if not opts.output_file:
        opts.output_file='%s.normalized.zip' %os.path.splitext(path)[0]
        logging.warning('No outputfile given (by option --output_file) using default output file "%s"' %opts.output_file)
    return opts, path


@contextmanager
def tempdir(directory='/dev/shm'):
    temp_folder = None
    try:
        temp_folder=tempfile.mkdtemp(dir=directory)
        yield temp_folder
    finally:
        shutil.rmtree(temp_folder)

def find_folder(filename,txtfile='agency.txt'):
    with ZipFile(filename) as z:
        filelist=z.namelist()
        if txtfile in filelist:
            logging.error('File is "%s" is in place. File "%s" does not require normalization. Exiting...' %(txtfile,filename))
            exit(1)
            return './'
        folders=set([os.path.split(x)[0] for x in z.namelist() if '/' in x])
        for f in folders:
            if '%s/%s' %(f,txtfile) in filelist:
                return f
        logging.error('No file named agency.txt found in zipfile "%s". Exiting...' %filename)
        exit(1)

def extract_and_recompress(filename,folder,output_filename='/tmp/out.zip'):
    with tempdir() as tmp:
        with ZipFile(filename) as z:
            z.extractall(tmp)
        files=glob.glob('%s/%s/*.txt' %(tmp,folder))
        with ZipFile(output_filename,'w') as o:
            for f in files:
                o.write(f,os.path.basename(f))
        logging.info(files)

if __name__ == '__main__':
    opts,path=options()

    folder=find_folder(path)
    extract_and_recompress(path,folder,opts.output_file)
