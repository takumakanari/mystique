# -*- encoding:utf8 -*-
from __future__ import absolute_import
import urwid
from mystique.log import logger


class AutoCompoleteEditor(urwid.Edit):
    pass


class QueryEditor(urwid.Edit):

    __allowed_callbacks = ('close', 'execute',)

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

