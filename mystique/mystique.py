# -*- encoding:utf8 -*-
from __future__ import absolute_import
import urwid
import blinker
import mystique
from mystique import config
from mystique.db import Database, Table
from mystique.session import TableSession, FreeQuerySession
from mystique.log import logger
from mystique.widgets import QueryEditor, MouseEvCanceledButton, TableFilter


palette = [
    ('body','black','light gray', 'standout'),
    ('reverse','light gray','black'),
    ('header','light red','dark blue', 'bold'),
    ('footer','light gray','black',),
    ('editcp','black','white', 'bold'),
    ('bright','dark gray','light gray', ('bold','standout')),
    ('buttn','black','dark cyan'),
    ('buttnf','black','light gray','bold'),
    ('col_head', 'dark green', 'black', 'bold'),
    ('error_message','dark red','white')
]


_kb_focus_on_g = (
    ('g', 'Focus to top'),
    ('G', 'Focus to bottom')
)

_kb_quit_on_q = (
    ('q(Q)', 'Quit'),
)

_kb_lr_pager = (
    ('right', 'Next page'),
    ('left', 'Prev page')
)

keybinds = {
    'keypress_default' : (
        ('x', 'Open query editor'),
        ('/', 'Open or close table filter'),
    ) + _kb_focus_on_g + _kb_quit_on_q,
    'keypress_in_table_session' : (
        ('q(Q)', 'Back to table list'),
        ('d', 'show open description')
    ) + _kb_focus_on_g + _kb_lr_pager,
    'keypress_in_table_desc' : (
        ('left/q/Q', 'Back to list'),
    ),
    'keypress_in_editor' : (
        ('ctrl b', 'Execute query'),
        ('ctrl x', 'Close query editor')
    ),
    'keypress_in_query_result' : (
        ('x', 'Reopen query editor'),
        ('ctrl x', 'Close query editor'),
        ('ctrl b', 'Execute query'),
        ('q', 'Back to table list')
    ) + _kb_focus_on_g + _kb_lr_pager
}


HEADER_DEFAULT = '%s %s' % (mystique.__mystique__, mystique.__version__)


def txt(v, weight=0, align='left'):
    d = urwid.Text(v or '', align=align)
    return d if not weight else ('weight', weight, d)


WG_COL_SEP = txt('|')


class Events(object):
    table_list_rendered = blinker.signal('table_list_rendered')
    table_desc_rendered = blinker.signal('table_desc_rendered')
    table_values_rendered = blinker.signal('table_values_rendered')
    query_result_rendered = blinker.signal('query_result_rendered')
    keybind_changed = blinker.signal('keybind_changed')


class MystyqFrame(urwid.Frame):

    def __init__(self, conf):
        self._config = conf
        self._database = Database(**conf['database'])
        self._table_list = self._database.show_tables()

        self.information_text1 = txt(self._database.connection_string)
        self.information_text2 = txt('')
        self.footer_text = txt('')
        self.listbox = urwid.ListBox(urwid.SimpleListWalker([]))
        self.query_editor = None
        self.table_filter = TableFilter(word_list=self._table_list,
                                       autocompleted=self._do_table_filter)
        self._keypress_handler = self.keypress_default
        self._table_session = None
        self._current_focus_on_tablelist = 0

        super(MystyqFrame, self).__init__(
            self.listbox,
            header = urwid.AttrWrap(urwid.Columns([
                urwid.Pile([self.information_text1, self.information_text2]),
                urwid.Text(HEADER_DEFAULT, align='right'),
            ]), 'header'),
            footer = urwid.AttrWrap(self.footer_text, 'footer')
        )

        self.render_table_list()

    def render_table_list(self):
        self._session = None
        self._change_keybinds(self.keypress_default)

        def button_press(b):
            table = b.get_label()
            self._current_focus_on_tablelist = self.listbox.focus_position
            logger.info('table=[%s] is choosen (focus: %d)' %
                        (table, self._current_focus_on_tablelist))

            self._session = TableSession(self._database.get_table(table))
            if self.render_table_values():
                self._change_keybinds(self.keypress_in_table_session)

            Events.table_values_rendered.send(self)

        self.clear_listbox()

        if not self.table_filter_is_shown and self.table_filter.is_active():
            self.toggle_table_filter(clear=False) # re-show table filter ...

        tables = self.table_filter.current_list
        if tables:
            min_len = max(len(x) for x in tables)
            for t in tables:
                btn = urwid.AttrWrap(MouseEvCanceledButton(t, button_press),
                                    'button', 'buttnf')
                btn = urwid.Padding(btn, align='left', min_width=min_len,
                                    width=('relative', min_len))
                self.listbox.body.append(btn)
            self.listbox.body.set_focus(self._current_focus_on_tablelist)
            self._current_focus_on_tablelist = 0

        Events.table_list_rendered.send(self)

    def render_table_values(self):
        try:
            result_list = self._session.get_list()
        except Exception as e:
            logger.error(e)
            self.render_error('%d: %s' % (e[0] or 0, e[1]))
            return False

        result_desc = self._session.result_desc()
        logger.debug('%s results in %s' % (len(result_list), str(result_desc)))

        names = (txt('', weight=1),) + tuple(txt(x, weight=2) for x in result_desc)
        header = urwid.AttrWrap(urwid.Columns(names), 'col_head')
        self.clear_listbox(body=[header])

        for c, values in enumerate(result_list):
            index_str = str(c + 1 + self._session.offset)
            line = (txt(index_str, weight=1),) + tuple(txt(v, weight=2) for v in values)
            self.listbox.body.append(urwid.Columns(line))

        Events.table_values_rendered.send(self)

        return True

    def render_error(self, msg):
        m = urwid.AttrWrap(txt('ERROR! %s' % msg), 'error_message')
        self.footer_text.set_text(msg)

    def render_table_desc(self):
        header_keys = ('name', 'type', 'nullable', 'key', 'default', 'extra')
        header = urwid.Columns(tuple(txt(x) for x in header_keys))
        self.clear_listbox([urwid.AttrWrap(header, 'col_head')])
        for d in self._session.table.desc:
            col = urwid.Columns(tuple(txt(d[x]) for x in header_keys))
            self.listbox.body.append(col)
        Events.table_desc_rendered.send(self)

    def execute_sql_in_query_editor(self):
        query = self.query_editor.get_query()
        if query:
            self._session = FreeQuerySession(self._database.cursor, query)
            if self.render_table_values():
                self._change_keybinds(self.keypress_in_query_result)
            return True
        return False

    def open_query_editor(self, default_query=None):
        self.query_editor = urwid.AttrWrap(QueryEditor('Query here ...\n',
                                          default_query or ''), 'editcp')
        self.clear_listbox(body=[self.query_editor])

    def toggle_table_filter(self, clear=True):
        if self.table_filter_is_shown:
            self.table_filter.reset()
            self.render_table_list()
        else:
            if clear:
                self.table_filter.clear()
            self.listbox.body.insert(0, self.table_filter)
            self.focus_to_top()

    def _do_table_filter(self, results):
        self.render_table_list()

    def keypress_default(self, size, key):
        if self.table_filter_is_shown:
            if key == '/':
                self.toggle_table_filter()
            return super(MystyqFrame, self).keypress(size, key)
        if key == 'x':
            self._current_focus_on_tablelist = self.listbox.focus_position
            self.open_query_editor()
            self._change_keybinds(self.keypress_in_editor)
            return
        elif key == '/':
            self.toggle_table_filter()
            return
        return self._common_keypresses(size, key, focus_on_g=True,
                                       exit_on_q=True)

    def keypress_in_table_session(self, size, key):
        if key in ('q', 'Q'):
            self.render_table_list()
            self._change_keybinds(self.keypress_default)
        elif key == 'd':
            self.render_table_desc()
            self._change_keybinds(self.keypress_in_table_desc)
        return self._common_keypresses(size, key,
                                       focus_on_g=True, lr_pager=True)

    def keypress_in_table_desc(self, size, key):
        if key in ('left', 'q', 'Q'):
            if self.render_table_values():
                self._change_keybinds(self.keypress_in_table_session)
        return super(MystyqFrame, self).keypress(size, key)

    def keypress_in_editor(self, size, key):
        if key == 'ctrl b':
            self.execute_sql_in_query_editor()
        elif key == 'ctrl x':
            self.query_editor = None
            self.render_table_list()
            self._change_keybinds(self.keypress_default)
        else:
            return super(MystyqFrame, self).keypress(size, key)

    def keypress_in_query_result(self, size, key):
        if self.query_editor_is_shown:
            if key == 'ctrl x':
                del self.listbox.body[0]
                return
            if key == 'ctrl b':
                self.execute_sql_in_query_editor()
            return super(MystyqFrame, self).keypress(size, key)
        if key == 'x': # re-open query editor
            self.listbox.body.insert(0, self.query_editor)
            return
        elif key == 'q':
            self.render_table_list()
        return self._common_keypresses(size, key,
                                       focus_on_g=True, lr_pager=True)

    def _common_keypresses(self, size, key, focus_on_g=False, exit_on_q=False,
                           lr_pager=False):
        if focus_on_g:
            if key == 'g':
                self.focus_to_top()
            elif key == 'G':
                self.focus_to_last()
        if exit_on_q and key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        if lr_pager:
            if key == 'right' and self._session.has_next:
                self._session.next_page()
                self.render_table_values()
            elif key == 'left' and self._session.has_prev():
                self._session.prev_page()
                self.render_table_values()
        return super(MystyqFrame, self).keypress(size, key)

    def keypress(self, size, key):
        return self._keypress_handler(size, key)

    def focus_to_top(self):
        self.listbox.body.set_focus(0)

    def focus_to_last(self):
        pos = len(self.listbox.body) - 1
        if pos > 0:
            self.listbox.body.set_focus(pos)

    def clear_listbox(self, body=[]):
        self.listbox.body[:] = urwid.SimpleListWalker(body)

    def update_information(self, v):
        self.information_text2.set_text(v or '')

    def update_keybind_information(self, keybinds):
        txts = []
        for conf in keybinds:
            txts.append('%s:%s' % (conf[0], conf[1]))
        self.footer_text.set_text('  '.join(txts))
        #self.footer_text.widget_list.append(txt('c'))
        #self.footer_text.render()

    def _change_keybinds(self, handle_func):
        self._keypress_handler = handle_func
        Events.keybind_changed.send(view=self, name=handle_func.__name__)
        logger.info('keypress handler is updated: %s' % handle_func.__name__)

    @property
    def session(self):
        return self._session

    @property
    def query_editor_is_shown(self):
        v = self.listbox.body[0]
        if isinstance(v, urwid.AttrWrap):
            return isinstance(v.original_widget, QueryEditor)
        return False

    @property
    def table_filter_is_shown(self):
        v = self.listbox.body and self.listbox.body[0]
        if isinstance(v, urwid.AttrWrap):
            return isinstance(v.original_widget, TableFilter)
        return v is not None and isinstance(v, TableFilter)


def info_of_session(view):
    view.update_information(str(view.session))


def info_of_table_desc(view):
    view.update_information('desc %s' % view.session.name())


def info_of_table_list(view):
    view.update_information('show tables')


def keybind_information_in_footer(*args, **kwargs):
    view, name = (kwargs['view'], kwargs['name'])
    view.update_keybind_information(keybinds[name])


def main():
    logger.debug('Bootup mystique...')
    Events.table_list_rendered.connect(info_of_table_list)
    Events.table_values_rendered.connect(info_of_session)
    Events.table_desc_rendered.connect(info_of_table_desc)
    Events.keybind_changed.connect(keybind_information_in_footer)
    view = MystyqFrame(config.load_config())
    urwid.MainLoop(view, palette).run()


if __name__ == '__main__':
    main()

