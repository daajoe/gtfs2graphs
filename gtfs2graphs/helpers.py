# -*- coding: utf-8 -*-
#import contextlib
import logging
from os.path import *
import yaml

def read_config(filename=__file__, config_dir=dirname(__file__), config_pattern='%s/conf/%s_conf.yaml'):
    print filename
    config_file = config_pattern %(config_dir, splitext(basename(realpath(filename)))[0])
    print config_file
    if basename(__file__) == 'helpers.py':
        return {}
    with open(config_file, 'r') as f:
        return yaml.load(f)

def setup_logging(config_file='%s/conf/logging.conf' %(dirname(__file__))):
    logging.config.fileConfig(config_file)

def nested_get(d, keys):
    try:
        return reduce(dict.__getitem__, keys, d)
    except TypeError, e:
        logging.debug('Received wrong format for keys: %s (dict: %s). Setting to "NA"', keys, d)
        return 'NA'
    except KeyError, e:
        if keys == ['u','d']:
            #logging.info('Proceeding with alternative key for url')
            return nested_get(d, ['u','i'])
        logging.error('Missing key: %s (dict: %s).', keys, d)


def chain_list(iterables):
    for it in iterables:
        if type(it) is list:
            for element in it:
                yield element
        else:
            yield it
