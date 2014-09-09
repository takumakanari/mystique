#!/usr/bin/env python
# -*- encoding:utf-8 -*-
from __future__ import absolute_import
import urwid
from mystique.widgets import _AutoComplete
from mystique.log import logger


class AcWordTypes(object):
    other = 0
    sql_reserved_word = 1
    column = 2
    table = 3


def with_word_type(words, word_type):
    return tuple(((x, word_type) for x in words))


class _QuerySyntaxAutoComplete(_AutoComplete):

    __autocompletable_min_len = 2

    __sql_words = ('absolute', 'action', 'add', 'all', 'allocate',
                  'alter', 'and', 'any', 'are', 'as', 'asc', 'assertion',
                  'at', 'authorization', 'avg', 'begin', 'between', 'bit',
                  'bit_length', 'both', 'by', 'cascade', 'cascaded', 'case',
                  'cast', 'catalog', 'char', 'character', 'character_length',
                  'char_length', 'check', 'close', 'coalesce', 'collate',
                  'collation', 'column', 'commit', 'connect', 'connection',
                  'constraint', 'constraints', 'continue', 'convert',
                  'corresponding', 'create', 'cross', 'current',
                  'current_date', 'current_time', 'current_timestamp',
                  'current_user', 'cursor', 'date', 'day', 'deallocate', 'dec',
                  'decimal', 'declare', 'default', 'deferrable', 'deferred',
                  'delete', 'desc', 'describe', 'descriptor', 'diagnostics',
                  'disconnect', 'distinct', 'domain', 'double', 'drop', 'else',
                  'end', 'end-exec', 'escape', 'except', 'exception', 'exec',
                  'execute', 'exists', 'external', 'extract', 'false', 'fetch',
                  'first', 'float', 'for', 'foreign', 'found', 'from', 'full',
                  'get', 'global', 'go', 'goto', 'grant', 'group', 'having',
                  'hour', 'identity', 'immediate', 'in', 'indicator',
                  'initially', 'inner', 'input', 'insensitive', 'insert',
                  'int', 'integer', 'intersect', 'interval', 'into', 'is',
                  'isolation', 'join', 'key', 'language', 'last', 'leading',
                  'left', 'level', 'like', 'local', 'lower', 'match', 'max',
                  'min', 'minute', 'module', 'month', 'names', 'national',
                  'natural', 'nchar', 'next', 'no', 'not', 'null', 'nullif',
                  'numeric', 'octet_length', 'of', 'on', 'only', 'open',
                  'option', 'or', 'order', 'outer', 'output', 'overlaps',
                  'preserve','pad', 'partial', 'position', 'precision',
                  'prepare', 'primary', 'prior', 'privileges', 'procedure',
                  'public', 'read', 'real', 'references', 'relative',
                  'restrict', 'revoke', 'right', 'rollback', 'rows', 'schema',
                  'scroll', 'second', 'section', 'select', 'session',
                  'session_user', 'set', 'size', 'smallint', 'some', 'space',
                  'sql', 'sqlcode', 'sqlerror', 'sqlstate', 'substring', 'sum',
                  'system_user', 'table', 'temporary','then', 'time',
                  'timestamp', 'timezone_hour', 'timezone_minute', 'to',
                  'trailing', 'transaction', 'translate', 'translation',
                  'trim', 'true', 'union', 'unique', 'unknown', 'update',
                  'upper', 'usage', 'user', 'using', 'value', 'values',
                  'varchar', 'varying', 'view', 'when', 'whenever', 'where',
                  'with', 'work', 'write', 'year', 'zone', 'count', 'count(*)',
                  'group by', 'order by')

    def __init__(self, *args, **kwargs):
        if 'custom_word_list' in kwargs:
            _custom_word_list = kwargs['custom_word_list'] or ()
            del kwargs['custom_word_list']
        else:
            _custom_word_list = ()
        word_list = with_word_type(self.__sql_words,
                                  AcWordTypes.sql_reserved_word) + \
                                  _custom_word_list
        kwargs.update(
            word_list = sorted(word_list, key=lambda x:x[1]),
            multiline = True
        )
        super(_QuerySyntaxAutoComplete, self).__init__(*args, **kwargs)
        self.edit_pos_from = -1
        self.edit_pos_to = -1

    def get_possible_word(self, val):
        self.edit_pos_from = -1
        self.edit_pos_to = -1
        val_len = len(val)
        pos = self.edit_pos
        if pos == val_len or (val_len > pos and val[pos] in (' ', '\n')):
            idx = pos - 1
            while idx >= 0:
                self.edit_pos_from = idx
                self.edit_pos_to = pos
                if val[idx] in (' ', '.', '\n'):
                    self.edit_pos_from = idx + 1
                    return val[self.edit_pos_from:self.edit_pos_to]
                idx -= 1
        if self.edit_pos_from > -1 and self.edit_pos_to > -1:
            return val[self.edit_pos_from:self.edit_pos_to]
        else:
            return None

    def insert(self, word):
        logger.debug('insert [%s] %d/%d' % (word, self.edit_pos_from,
                                            self.edit_pos_to))
        t = self.get_edit_text()
        buf = []
        if self.edit_pos_from > 0:
            buf.append(t[:self.edit_pos_from])
        buf.append(word)
        if self.edit_pos_to > 0:
            buf.append(t[self.edit_pos_to:])
        self.set_edit_text(''.join(buf))
        self.set_edit_pos(self.edit_pos_from + len(word) + 1)

    def do_filter(self, val):
        possible_word = self.get_possible_word(val)
        if not possible_word or \
            len(possible_word) < self.__autocompletable_min_len:
                return []
        possible_word = possible_word.lower()
        logger.debug('possible_word: "%s"' % possible_word)

        def _match(v):
            vl = v[0].lower()
            return vl.startswith(possible_word) and \
                vl != possible_word

        return filter(_match, self.word_list)


class QuerySuggention(urwid.Columns):

    def __init__(self, words=(), editor=None, on_select=None):
        self._editor = editor
        self._on_select = on_select
        self.update(words or [('', AcWordTypes.other)])

    def update(self, words):
        super(QuerySuggention, self).__init__(self._make_data(words),
                                             dividechars=1)

    def keypress(self, size, key):
        if key == 'tab':
            pos = self.focus_position
            if len(self.widget_list) > pos + 1:
                self.set_focus(pos + 1)
            else:
                self.set_focus(0)
        elif key == 'enter':
            if self._editor:
                t = self.widget_list[self.focus_position].get_text()[0]
                logger.debug('"%s" => %s' % (t, self._editor))
                self._editor.insert(t)
                if self._on_select:
                    self._on_select()
        return super(QuerySuggention, self).keypress(size, key)

    @classmethod
    def _make_data(cls, words):
        def _s(x):
            v, word_type = x # {AcWordTypes}
            w = urwid.AttrWrap(urwid.SelectableIcon(v, 0),
                              'buttn-%s' % word_type, 'buttnf')
            return ('fixed', len(v), w)
        return tuple(_s(x) for x in words)


class QueryEditor(urwid.Pile):

    def __init__(self, query=None, custom_word_list=()):
        editor = _QuerySyntaxAutoComplete('', query or '',
                                          autocompleted=self._autocompleted,
                                          custom_word_list=custom_word_list)
        qs = QuerySuggention(editor=editor, on_select=self.focus_to_top)
        self._editor = urwid.LineBox(urwid.AttrWrap(editor, 'editcp'), 'SQL')
        self._suggestionbox = urwid.LineBox(qs)
        super(QueryEditor, self).__init__([self._editor])

    def get_query(self):
        ow = self._editor.original_widget
        return self.optimize_query(ow.get_edit_text())

    def keypress(self, size, key):
        if key == 'tab' and self.suggestbox_is_shown and \
            self.focus_position == 0:
                self.focus_to_suggestionbox()
                return
        return super(QueryEditor, self).keypress(size, key)

    def focus_to_top(self):
        self.set_focus(0)

    def focus_to_suggestionbox(self):
        if self.suggestbox_is_shown:
            self.set_focus(1)

    @property
    def suggestbox_is_shown(self):
        return len(self.widget_list) >= 2

    def _autocompleted(self, results):
        if not results:
            if self.suggestbox_is_shown:
                del self.widget_list[1]
        else:
            self._suggestionbox.original_widget.update(results)
            if not self.suggestbox_is_shown:
                self.widget_list.append(self._suggestionbox)

    @classmethod
    def optimize_query(cls, src):
        return src.strip()

