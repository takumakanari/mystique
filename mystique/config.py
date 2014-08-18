# -*- encoding:utf8 -*-
from __future__ import absolute_import
import os
import json
from mystique.log import logger

DEFAULT_CONFIG_NAME = 'mystique.config'
CONFIG_LOAD_DIR = ('.', '/etc/mystique')
CONFIG_FILE_IN_ENV = os.environ.get('MYSTIQUE_CONFIG')


def load_config():
    path = CONFIG_FILE_IN_ENV
    if not path:
        for d in CONFIG_LOAD_DIR:
            path = os.path.join(d, DEFAULT_CONFIG_NAME)
            if os.path.exists(path):
                break
    if not path:
        raise Exception('Can not load mystique.config in %s' % str(CONFIG_LOAD_DIR))
    logger.info('config load from %s' % path)
    return json.load(open(path))

