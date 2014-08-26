# -*- encoding:utf8 -*-
from __future__ import absolute_import

from mystique import env
import logging
import os


if env.MYSTIQUE_ENV_LOG_DEBUG or env.MYSTIQUE_ENV_LOG_FILE:
    logfile = env.MYSTIQUE_ENV_LOG_FILE if env.MYSTIQUE_ENV_LOG_FILE \
        else '/tmp/mystique.log'
    level = logging.DEBUG if env.MYSTIQUE_ENV_LOG_DEBUG else logging.INFO
    logging.basicConfig(filename=logfile,level=level)


logger = logging
