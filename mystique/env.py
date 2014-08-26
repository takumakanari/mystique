# -*- encoding:utf8 -*-
from __future__ import absolute_import
import os


MYSTIQUE_ENV_CONFIG_FILE = os.environ.get('MYSTIQUE_CONFIG')

MYSTIQUE_ENV_LOG_DEBUG = os.environ.get('MYSTIQUE_LOG_DEBUG') == '1'

MYSTIQUE_ENV_LOG_FILE = os.environ.get('MYSTIQUE_LOG_FILE')
