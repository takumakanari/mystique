# -*- encoding:utf8 -*-
from __future__ import absolute_import

import MySQLdb
from contextlib import closing, contextmanager
from mystique.log import logger


def value_optimize(v):
    if v is None:
        return ''
    elif not isinstance(v, basestring):
        return str(v)
    return v


class _ConnectableMixin(object):

    """ must be called this function first """
    def set_config(self, config):
        self._config = config

    @contextmanager
    def new_cursor(self):
        with closing(MySQLdb.connect(**self._config)) as conn:
            with closing(conn.cursor()) as cursor:
                yield cursor


class Database(_ConnectableMixin):

    def __init__(self, **config):
        logger.info('[DB] config: %s' % str(config))
        self._config = config
        self.set_config(self._config)

    def config(self, name):
        return self._config[name]

    def show_tables(self):
        with self.new_cursor() as cursor:
            cursor.execute('show tables')
            ret = map(lambda x:x[0], cursor.fetchall())
        return ret

    def get_table(self, name):
        return Table(self._config, name)

    def show_databases(self):
        with self.new_cursor() as cursor:
            cursor.execute('show databases')
            ret = map(lambda x:x[0], cursor.fetchall())
        return ret

    @property
    def connection_string(self):
        return '%s@%s:%d %s' % (self.config('user'), self.config('host'),
                                self.config('port'), self.config('db'))


class Table(_ConnectableMixin):

    def __init__(self, config, name):
        self.set_config(config)
        self.name = name
        self._desc = None

    def simple_list(self, offset=0, limit=100):
        with self.new_cursor() as cursor:
            cursor.execute('select * from %s limit %d offset %d' % \
                           (self.name, limit, offset))
            dest = []
            for values in iter(cursor):
                col = []
                for v in values:
                    col.append(value_optimize(v))
                dest.append(col)
        return dest

    @property
    def desc(self):
        if not self._desc:
            with self.new_cursor() as cursor:
                cursor.execute('desc %s' % self.name)
                self._desc = []
                for c in iter(cursor):
                    data = dict(
                     name = c[0],
                     type = c[1],
                     nullable = c[2],
                     key = c[3],
                     default = c[4] or 'NULL',
                     extra = c[5]
                )
                    self._desc.append(data)
        return self._desc

