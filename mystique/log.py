# -*- encoding:utf8 -*-
from __future__ import absolute_import

import logging
import os

_log_dir = '/tmp'
_log_file = os.path.join(_log_dir, 'mystique.log')

logging.basicConfig(filename=_log_file,level=logging.DEBUG)

logger = logging
