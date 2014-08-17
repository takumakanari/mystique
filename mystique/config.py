# -*- encoding:utf8 -*-
from __future__ import absolute_import
import os
import json
from mystique.log import logger

CONFIG_NAME = 'mystique.config'
CONFIG_LOAD_DIR = ('.', '/etc/mystique')

if os.environ.get('MYSTIQUE_CONFIG_DIR'):
    CONFIG_LOAD_DIR += (os.environ['MYSTIQUE_CONFIG_DIR'],)


def load_config():
    for d in CONFIG_LOAD_DIR:
        path = os.path.join(d, CONFIG_NAME)
        if os.path.exists(path):
            logger.info('config load from %s' % path)
            return json.load(open(path))
    raise Exception('Can not load mystique.config in %s' % str(CONFIG_LOAD_DIR))

