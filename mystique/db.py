# -*- encoding:utf8 -*-
from __future__ import absolute_import

import MySQLdb
from mystique.log import logger


def value_optimize(v):
    if v is None:
        return ''
    elif not isinstance(v, basestring):
        return str(v)
    return v


class Database(object):

    default_limit = 100

    def __init__(self, **config):
        logger.info('[DB] connect: %s' % str(config))
        self._config = config
        self.db = MySQLdb.connect(**self._config)
        self.cursor = self.new_cursor()

    def new_cursor(self):
        return self.db.cursor()

    def config(self, name):
        return self._config[name]

    def show_tables(self):
        self.cursor.execute('show tables')
        return map(lambda x:x[0], self.cursor.fetchall())

    def get_table(self, name):
        return Table(self.cursor, name)

    def show_databases(self):
        self.cursor.execute('show databases')
        return map(lambda x:x[0], self.cursor.fetchall())

    @property
    def connection_string(self):
        return '%s@%s:%d %s' % (self.config('user'), self.config('host'),
                                self.config('port'), self.config('db'))


class Table(object):

    default_limit = 100

    def __init__(self, cursor, name):
        self.cursor = cursor
        self.name = name
        self._desc = None

    def simple_list(self, offset=0, limit=100):
        self.cursor.execute('select * from %s limit %d offset %d' % (self.name, limit, offset))
        dest = []
        for values in self.cursor.fetchall():
            col = []
            for v in values:
                col.append(value_optimize(v))
            dest.append(col)
        return dest

    @property
    def desc(self):
        if not self._desc:
            self.cursor.execute('desc %s' % self.name)
            self._desc = []
            for c in self.cursor.fetchall():
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

#database = Database()
