# -*- encoding:utf8 -*-
from __future__ import absolute_import


def get_once(data, key, default=None):
    v = data.get(key)
    if key in data:
        del data[key]
    return v or default
