# -*- encoding:utf8 -*-
from __future__ import absolute_import
from mystique.log import logger
from mystique.db import value_optimize
import os


class _Session(object):

    def __init__(self):
        self.offset = 0
        self.limit = 100
        self._has_next = False

    def next_page(self):
        self.offset += self.limit

    def prev_page(self):
        self.offset -= self.limit

    def has_prev(self):
        return self.offset > 0

    @property
    def index_from_1(self):
        return self.offset + 1

    @property
    def has_next(self):
        return self._has_next

    def get_list(self):
        return []

    def result_desc(self):
        return []

    def close(self):
        pass

    def name(self):
        return self.__str__()

    def word_list(self):
        return ()

    def default_query(self):
        return None

    def __str__(self):
        return str(self.__class__)


class TableSession(_Session):

    def __init__(self, table):
        self.table = table
        super(TableSession, self).__init__()
        self._result_size = 0

    def word_list(self):
        return tuple(self.result_desc())

    def get_list(self):
        ret = self.table.simple_list(offset=self.offset, limit=self.limit+1)
        self._result_size = len(ret)
        self._has_next = self._result_size > self.limit
        if self._has_next:
            del ret[self._result_size - 1]
            self._result_size -= 1
        return ret

    def word_list(self):
        return tuple(self.result_desc())

    def result_desc(self):
        return (x['name'] for x in self.table.desc)

    def name(self):
        return self.table.name

    def default_query(self):
        return 'select * from %s limit %d' % (self.table.name, self.limit)

    def __str__(self):
        if self._result_size:
            return '%s:%d-%d' % \
                (self.table.name, self.index_from_1,
                 self.index_from_1 + self._result_size - 1)
        else:
            return '%s:empty' % (self.table.name)


class FreeQuerySession(_Session):

    __query_digest_max_len = 80

    def __init__(self, database, query):
        super(FreeQuerySession, self).__init__()
        self._database = database
        self.query = query
        self._current_result_desc = None
        logger.info('init session: %s' % self.query)

    def word_list(self):
        return self._current_result_desc \
            if self._current_result_desc is not None else ()

    def get_list(self):
        with self._database.new_cursor() as cursor:
            cursor.execute(self.query)
            self._current_result_desc = tuple(x[0] for x in cursor.description)

            idx = 0
            ret = []
            for values in iter(cursor):
                if idx >= self.offset:
                    ret.append(tuple(value_optimize(v) for v in values))
                    if len(ret) > self.limit: # fetch until limit + 1
                        break
                idx += 1

            self._has_next = len(ret) > self.limit
            if self._has_next:
                del ret[len(ret) - 1]

        return ret

    def default_query(self):
        return self.query

    def result_desc(self):
        if self._current_result_desc is None:
            raise Exception('Illegal state, query is not executed in cursor!')
        return self._current_result_desc

    def __str__(self):
        dest = ' '.join(self.query.split(os.linesep))
        if len(dest) <= self.__query_digest_max_len:
            return dest
        return '%s ...' % (dest[:self.__query_digest_max_len])

