# -*- encoding:utf8 -*-
from __future__ import absolute_import
import os
import yaml

from mystique import env
from mystique.log import logger


DEFAULT_CONFIG_NAMES = ('mystique.yaml', 'mystique.yml',)
CONFIG_LOAD_DIR = ('.', '/etc/mystique')


class ConfigError(Exception):
    pass


def _estimate_config_path():
    for d in CONFIG_LOAD_DIR:
        for n in DEFAULT_CONFIG_NAMES:
            path = os.path.join(d, n)
            if os.path.exists(path):
                return path
    return None


def load_config(opts):
    path = opts.config or env.MYSTIQUE_ENV_CONFIG_FILE \
        or _estimate_config_path()
    if not path:
        raise ConfigError('Can not find configuration from %s in %s' % \
            ('|'.join(DEFAULT_CONFIG_NAMES), '|'.join(CONFIG_LOAD_DIR)))
    logger.info('load config: path=%s' % path)

    config = yaml.load(open(path))

    # TODO validate config schema
    aliases = config and config.keys()
    if not aliases:
        raise ConfigError('Configuration is empty!')
    elif not opts.name and len(aliases) > 1:
        raise ConfigError('Specify one name from %s for connection alias' % '|'.join(aliases))
    elif opts.name and opts.name not in aliases:
        raise ConfigError('Name "%s" is not found in %s' % (opts.name, path))

    config = config[aliases[0]] if len(aliases) == 1 else config[opts.name]

    if opts.db:
        config['db'] = opts.db

    return config
