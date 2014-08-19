# -*- encoding:utf8 -*-
from __future__ import absolute_import
import urwid
from mystique.log import logger


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

    def clear_me(self):
        self.widget_list[:] = [_DummyTxt()]


class AutoCompoleteEditor(urwid.Edit):
    pass


class QueryEditor(urwid.Edit):

    def __init__(self, *args, **kwargs):
        kwargs.update(multiline=True)
        super(QueryEditor, self).__init__(*args, **kwargs)

    def get_query(self):
        return self.optimize_query(self.get_edit_text())

    @classmethod
    def optimize_query(cls, src):
        return src.strip()


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

    @property
    def word_list(self):
        return self._word_list
    
    @property
    def current_list(self):
        return self._current_list

    def clear(self):
        self.set_edit_text('')

    def reset(self):
        self.clear()
        self._current_list = self._word_list

    def is_active(self):
        return True if self.get_edit_text().strip() else False

    def keypress(self, size, key):
        kp = super(_AutoComplete, self).keypress(size, key)
        if self._autocompleted:
            txt = self.get_edit_text().strip()
            self._current_list = self.do_filter(txt)
            self._autocompleted(self._current_list)
        return kp

    def do_filter(self, val):
        return filter(lambda x:x.lower().startswith(val.lower()),
                      self.word_list)


class TableFilter(_AutoComplete):
    pass

