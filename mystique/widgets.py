# -*- encoding:utf8 -*-
from __future__ import absolute_import
import urwid
from mystique.log import logger


def txt(v, weight=0, align='left'):
    d = urwid.Text(v or '', align=align)
    return d if not weight else ('weight', weight, d)


def ftxt(v, s):
    return ('fixed', s, txt(v))


class _OriginalWidgetWrapMixin(object):

    def __getattribute__(self, name):
        try:
            return super(_OriginalWidgetWrapMixin,self).__getattribute__(name)
        except AttributeError:
            return self.original_widget.__getattribute__(name)


def wrap_widget(cls, *args, **kwargs):
    class _Wrapped(cls, _OriginalWidgetWrapMixin):
        pass
    return _Wrapped(*args, **kwargs)


class _DummyTxt(urwid.Text):

    def __init__(self):
        super(_DummyTxt, self).__init__('')


class AppendableColumns(urwid.Columns):

    def __init__(self, widget_list):
        if len(widget_list):
            super(AppendableColumns, self).__init__(widget_list)
        else:
            super(AppendableColumns, self).__init__([_DummyTxt()])

    def optimize_me(self):
        if len(self.widget_list) and isinstance(self.widget_list[0], _DummyTxt):
            del self.widget_list[0]

    def replace_me(self, *widget_list):
        self.widget_list[:] = widget_list

    def clear_me(self):
        self.widget_list[:] = [_DummyTxt()]


class AutoCompoleteEditor(urwid.Edit):
    pass


class MouseEvCanceledButton(urwid.Button):
    """Skips any mouse event"""
    def mouse_event(self, size, event, button, x, y, focus):
        pass


class ErrorMessage(urwid.Text):

    def __init__(self, msg):
        super(ErrorMessage, self).__init__('ERROR! %s' % msg)


class _AutoComplete(urwid.Edit):

    def __init__(self, *args, **kwargs):
        self._word_list = kwargs.get('word_list') or []
        self._current_list = self._word_list
        self._autocompleted = kwargs.get('autocompleted')
        if 'word_list' in kwargs:
            del kwargs['word_list']
        if 'autocompleted' in kwargs:
            del kwargs['autocompleted']
        super(_AutoComplete, self).__init__(*args, **kwargs)
        self._last_txt = self.get_edit_text()
        self._is_active = False

    @property
    def word_list(self):
        return self._word_list

    @property
    def current_list(self):
        return self._current_list

    def get_edit_text(self, *args, **kwargs):
        return super(_AutoComplete, self).\
            get_edit_text(*args, **kwargs).strip()

    def clear(self):
        self.set_edit_text('')

    def reset(self):
        self.clear()
        self._current_list = self._word_list

    def activate(self):
        self._is_active = True

    def deactivate(self):
        self._is_active = False

    def is_active(self):
       return self._is_active

    def keypress(self, size, key):
        kp = super(_AutoComplete, self).keypress(size, key)
        if self._autocompleted:
            txt = self.get_edit_text()
            if txt != self._last_txt:
                self._current_list = self.do_filter(txt)
                self._last_txt = txt
                self._autocompleted(self._current_list)
        return kp

    def do_filter(self, val):
        return filter(lambda x:x.lower().startswith(val.lower()),
                      self.word_list)


class TableFilter(urwid.LineBox):

    def __init__(self, *args, **kwargs):
        self.body = _AutoComplete(*args, **kwargs)
        super(TableFilter, self).__init__(self.body)


class _QuerySyntaxAutoComplete(_AutoComplete):

    _sql_words = ('absolute', 'action', 'add', 'all', 'allocate',
                  'alter', 'and', 'any', 'are', 'as', 'asc', 'assertion',
                  'at', 'authorization', 'avg', 'begin', 'between', 'bit',
                  'bit_length', 'both', 'by', 'cascade', 'cascaded', 'case',
                  'cast', 'catalog', 'char', 'character', 'character_length',
                  'char_length', 'check', 'close', 'coalesce', 'collate', 'collation',
                  'column', 'commit', 'connect', 'connection', 'constraint', 'constraints',
                  'continue', 'convert', 'corresponding', 'create', 'cross', 'current',
                  'current_date', 'current_time', 'current_timestamp', 'current_user',
                  'cursor', 'date', 'day', 'deallocate', 'dec', 'decimal', 'declare',
                  'default', 'deferrable', 'deferred', 'delete', 'desc', 'describe',
                  'descriptor', 'diagnostics', 'disconnect', 'distinct', 'domain', 'double',
                  'drop', 'else', 'end', 'end-exec', 'escape', 'except', 'exception', 'exec',
                  'execute', 'exists', 'external', 'extract', 'false', 'fetch', 'first', 'float',
                  'for', 'foreign', 'found', 'from', 'full', 'get', 'global', 'go', 'goto',
                  'grant', 'group', 'having', 'hour', 'identity', 'immediate', 'in', 'indicator',
                  'initially', 'inner', 'input', 'insensitive', 'insert', 'int', 'integer', 'intersect',
                  'interval', 'into', 'is', 'isolation', 'join', 'key', 'language', 'last', 'leading',
                  'left', 'level', 'like', 'local', 'lower', 'match', 'max', 'min', 'minute', 'module',
                  'month', 'names', 'national', 'natural', 'nchar', 'next', 'no', 'not', 'null', 'nullif',
                  'numeric', 'octet_length', 'of', 'on', 'only', 'open', 'option', 'or', 'order', 'outer',
                  'output', 'overlaps', 'pad', 'partial', 'position', 'precision', 'prepare', 'preserve',
                  'primary', 'prior', 'privileges', 'procedure', 'public', 'read', 'real', 'references',
                  'relative', 'restrict', 'revoke', 'right', 'rollback', 'rows', 'schema', 'scroll', 'second',
                  'section', 'select', 'session', 'session_user', 'set', 'size', 'smallint', 'some', 'space',
                  'sql', 'sqlcode', 'sqlerror', 'sqlstate', 'substring', 'sum', 'system_user', 'table', 'temporary',
                  'then', 'time', 'timestamp', 'timezone_hour', 'timezone_minute', 'to', 'trailing', 'transaction',
                  'translate', 'translation', 'trim', 'true', 'union', 'unique', 'unknown', 'update', 'upper', 'usage',
                  'user', 'using', 'value', 'values', 'varchar', 'varying', 'view', 'when', 'whenever', 'where', 'with',
                  'work', 'write', 'year', 'zone', 'count', 'count(*)', 'group by', 'order by')

    def __init__(self, *args, **kwargs):
        if 'custom_word_list' in kwargs:
            _custom_word_list = kwargs['custom_word_list'] or ()
            del kwargs['custom_word_list']
        else:
            _custom_word_list = ()
        kwargs.update(
            word_list = self._sql_words + _custom_word_list,
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
        if not possible_word or len(possible_word) < 2:
            return []
        possible_word = possible_word.lower()
        logger.debug('possible_word: "%s"' % possible_word)
        return filter(lambda x:x.lower().startswith(possible_word),
                      self.word_list)


class QueryEditor(urwid.LineBox):

    def __init__(self, query=None, title='SQL', attr='editcp',
                 custom_word_list=(), autocompleted=None, on_tab=None):
        editor = _QuerySyntaxAutoComplete('', query or '', autocompleted=autocompleted,
                                          custom_word_list=custom_word_list)
        self.body = urwid.AttrWrap(editor, attr)
        self._on_tab = on_tab
        super(QueryEditor, self).__init__(self.body, title)

    def get_query(self):
        return self.optimize_query(self.body.get_edit_text())

    def keypress(self, size, key):
        if key == 'tab' and self._on_tab:
            self._on_tab()
            return
        return super(QueryEditor, self).keypress(size, key)

    @classmethod
    def optimize_query(cls, src):
        return src.strip()


class QuerySuggention(urwid.Columns):

    def __init__(self, words=(), query_editor=None, on_select=None):
        self.query_editor = query_editor
        self._on_select = on_select
        self.update(words or [''])

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
            if self.query_editor:
                t = self.widget_list[self.focus_position].get_text()[0]
                logger.debug('"%s" => %s' % (t, self.query_editor))
                self.query_editor.body.insert(t)
                if self._on_select:
                    self._on_select()
        return super(QuerySuggention, self).keypress(size, key)

    @classmethod
    def _make_data(cls, words):
        def _s(x):
            return urwid.AttrWrap(urwid.SelectableIcon(x, 0),
                                 'button', 'buttnf')
        return tuple(('fixed', len(x), _s(x)) for x in words)


class QuerySuggentionBox(urwid.LineBox):

    def __init__(self, *args, **kwargs):
        self.body = QuerySuggention(*args, **kwargs)
        super(QuerySuggentionBox, self).__init__(self.body)

