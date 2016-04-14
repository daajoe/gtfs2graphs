# -*- coding: utf-8 -*-
import logging

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
