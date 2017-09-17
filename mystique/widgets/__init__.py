# -*- encoding:utf8 -*-
from __future__ import absolute_import

import urwid

from mystique.log import logger
from mystique import util


def txt(v, weight=0, align='left'):
    d = urwid.Text(v or '', align=align)
    return d if not weight else ('weight', weight, d)


def ftxt(v, s):
    return ('fixed', s, txt(v))


def fstxt(val, size):
    s = urwid.SelectableIcon(val, 0)
    return ('fixed', size, s)


def get_original_widget(src):
    return src.original_widget \
        if isinstance(src, urwid.AttrWrap) else src


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


class StupidButton(urwid.Button):
    """Skips any mouse event"""
    def mouse_event(self, size, event, button, x, y, focus):
        pass


class ErrorMessage(urwid.Text):

    def __init__(self, msg):
        super(ErrorMessage, self).__init__('ERROR! %s' % msg)


class _AutoComplete(urwid.Edit):

    def __init__(self, *args, **kwargs):
        self._word_list = util.get_once(kwargs, 'word_list', default=[])
        self._current_list = self._word_list
        self._autocompleted = util.get_once(kwargs, 'autocompleted')
        self._match_partical = util.get_once(kwargs, 'match_partical', default=False)
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
        if self._match_partical:
            matcher = lambda x:val.lower() in x.lower()
        else:
            matcher = lambda x:x.lower().startswith(val.lower())
        return filter(matcher, self.word_list)


class TableFilter(urwid.LineBox):

    def __init__(self, *args, **kwargs):
        self.body = _AutoComplete(*args, **kwargs)
        super(TableFilter, self).__init__(self.body)


class TableColumn(urwid.Columns):

    def __init__(self, widget_list):
        super(TableColumn, self).__init__(widget_list, dividechars=2)
