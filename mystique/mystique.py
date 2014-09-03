# -*- encoding:utf8 -*-
from __future__ import absolute_import
import urwid
import blinker
import mystique
from mystique import config
from mystique.db import Database, Table
from mystique.session import TableSession, FreeQuerySession
from mystique.log import logger
from mystique.widgets import AppendableColumns, StupidButton, \
TableFilter, TableColumn, txt, ftxt, fstxt, get_original_widget
from mystique.widgets.queryeditor import QueryEditor


palette = [
    # name, foreground color, background color
    ('body','black','light gray', 'standout'),
    ('reverse','light gray','black'),
    ('header','light red','dark blue', 'bold'),
    ('footer','light gray','black',),
    ('editcp','white','black'),
    ('bright','dark gray','light gray', ('bold','standout')),
    ('buttn','black','dark cyan'),
    ('buttnf','dark blue','yellow','bold'),
    ('col_head', 'dark green', 'black', 'bold'),
    ('error_message','light red','white'),
    ('kb_desc_cmd', 'yellow', 'dark blue')
]


_kb_focus_on_g = (
    ('g', 'Top'),
    ('G', 'Bottom')
)

_kb_quit_on_q = (
    ('q(Q)', 'Quit'),
)

_kb_lr_pager = (
    ('k', 'Next'),
    ('j', 'Prev')
)

keybinds = {
    'keypress_default' : (
        ('x', 'Query'),
        ('/', 'Filter'),
        ('esc', 'CloseFilter'),
    ) + _kb_focus_on_g + _kb_quit_on_q,
    'keypress_in_table_session' : (
        ('q(Q)', 'Close'),
        ('d', 'Description'),
        ('x', 'Query'),
        ('ctrl+x', 'Run'),
        ('esc', 'CloseEditor')
    ) + _kb_focus_on_g + _kb_lr_pager,
    'keypress_in_table_desc' : (
        ('q(Q)', 'Close'),
    ) + _kb_focus_on_g,
    'keypress_in_editor' : (
        ('ctrl+x', 'Run'),
        ('esc', 'Close')
    ),
    'keypress_in_query_result' : (
        ('x', 'Query'),
        ('ctrl+x', 'Run'),
        ('esc', 'CloseEditor'),
        ('q', 'Close')
    ) + _kb_focus_on_g + _kb_lr_pager
}


HEADER_DEFAULT = '%s %s' % (mystique.__mystique__, mystique.__version__)


class Events(object):
    table_list_rendered = blinker.signal('table_list_rendered')
    table_desc_rendered = blinker.signal('table_desc_rendered')
    table_values_rendered = blinker.signal('table_values_rendered')
    query_editor_opened = blinker.signal('query_editor_opened')
    query_result_rendered = blinker.signal('query_result_rendered')
    keybind_changed = blinker.signal('keybind_changed')


class MystiqueView(urwid.Frame):

    __max_width_each_column = 30

    def __init__(self, conf):
        self._config = conf
        self._database = Database(**conf['database'])
        self._table_list = self._database.show_tables()

        self.information_text1 = txt(self._database.connection_string)
        self.information_text2 = txt('')
        self.footer_columns = AppendableColumns([])
        self.listbox = urwid.ListBox(urwid.SimpleListWalker([]))
        self.query_editor = None
        self.table_filter = TableFilter(word_list=self._table_list,
                                       autocompleted=self._do_table_filter)
        self._keypress_handler = self.keypress_default
        self._table_session = None
        self._current_focus_on_tablelist = 0

        super(MystiqueView, self).__init__(
            self.listbox,
            header = urwid.AttrWrap(urwid.Columns([
                urwid.Pile([self.information_text1, self.information_text2]),
                urwid.Text(HEADER_DEFAULT, align='right'),
            ]), 'header'),
            footer = urwid.AttrWrap(self.footer_columns, 'footer')
        )

        self.render_table_list()

    @property
    def db_name(self):
        return self._database.config('db')

    def _start_table_session(self, table):
        self._current_focus_on_tablelist = self.listbox.focus_position
        logger.info('table=[%s] is choosen (focus: %d)' %
                    (table, self._current_focus_on_tablelist))
        self._session = TableSession(self._database.get_table(table))
        if self.render_table_values():
            self._change_keybinds(self.keypress_in_table_session)
        Events.table_values_rendered.send(self)

    def render_table_list(self):
        self._session = None
        self._change_keybinds(self.keypress_default)
        self.clear_listbox()

        if not self.table_filter_is_shown and \
            self.table_filter.body.is_active():
                self.open_table_filter(clear=False) # re-show table filter

        tables = self.table_filter.body.current_list
        if tables:
            max_len = max(len(x) for x in tables)
            new_session = lambda b:self._start_table_session(b.get_label())
            for t in tables:
                btn = urwid.AttrWrap(StupidButton(t, new_session),
                                    'button', 'buttnf')
                btn = urwid.Padding(btn, align='left',
                                    width=('relative', max_len))
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

        result_desc = tuple(self._session.result_desc())
        idx_col_len = len(str(len(result_list) + self._session.offset))

        sizemap = self._update_sizemap(result_desc, {},
                                       self.__max_width_each_column)
        for values in result_list:
            self._update_sizemap(values, sizemap, self.__max_width_each_column)

        names = (ftxt('', idx_col_len),) + \
            tuple(fstxt(x, sizemap[i]) for i, x in enumerate(result_desc))
        header = urwid.AttrWrap(TableColumn(names), 'col_head')
        self.clear_listbox(body=[header])

        for c, values in enumerate(result_list):
            index_str = str(c + 1 + self._session.offset)
            line = (ftxt(index_str, idx_col_len),) + \
                tuple(fstxt(v, sizemap[i]) for i, v in enumerate(values))
            self.listbox.body.append(TableColumn(line))

        Events.table_values_rendered.send(self)

        return True

    def render_error(self, msg):
        m = urwid.AttrWrap(txt('Ooops! %s' % msg), 'error_message')
        self.footer_columns.replace_me(m)

    def render_table_desc(self):
        header_keys = ('name', 'type', 'nullable', 'key', 'default', 'extra')
        header = urwid.Columns(tuple(txt(x) for x in header_keys), dividechars=1)
        self.clear_listbox([urwid.AttrWrap(header, 'col_head')])
        for d in self._session.table.desc:
            col = urwid.Columns(tuple(txt(d[x]) for x in header_keys), dividechars=1)
            self.listbox.body.append(col)
        Events.table_desc_rendered.send(self)

    def execute_sql_in_query_editor(self):
        query = self.query_editor.get_query()
        if query:
            self._session = FreeQuerySession(self._database, query)
            if self.render_table_values():
                self._change_keybinds(self.keypress_in_query_result)
            return True
        return False

    def open_query_editor(self, query=None, insert_top=False):
        wordlist = tuple(self._table_list)
        if self.session is not None:
            wordlist += self.session.word_list()
        self.query_editor = QueryEditor(query=query, custom_word_list=wordlist)
        if insert_top:
            self.listbox.body.insert(0, self.query_editor)
        else:
            self.clear_listbox(body=[self.query_editor])
        self.focus_to_top()
        Events.query_editor_opened.send(self)

    def open_table_filter(self, clear=True):
        if clear:
            self.table_filter.body.clear()
        if not self.table_filter_is_shown:
            self.listbox.body.insert(0, self.table_filter)
        self.table_filter.body.activate()
        self.focus_to_top()

    def close_table_filter(self):
        self.table_filter.body.reset()
        self.table_filter.body.deactivate()
        self.render_table_list()

    def _do_table_filter(self, results):
        self.render_table_list()

    def keypress_default(self, size, key):
        if self.table_filter_is_shown:
            if key == '/':
                self.open_table_filter(clear=False)
                return
            elif key == 'esc':
                self.close_table_filter()
            return super(MystiqueView, self).keypress(size, key)
        if key == 'x':
            self._current_focus_on_tablelist = self.listbox.focus_position
            self.open_query_editor()
            self._change_keybinds(self.keypress_in_editor)
            return
        elif key == '/':
            self.open_table_filter()
            return
        return self._common_keypresses(size, key, focus_on_g=True,
                                       exit_on_q=True)

    def keypress_in_table_session(self, size, key):
        if self.query_editor_is_shown:
            if key == 'esc':
                del self.listbox.body[0]
                Events.table_values_rendered.send(self)
            elif key == 'ctrl x':
                self.execute_sql_in_query_editor()
            return self._common_keypresses(size, key, scrollable=True)
        if key in ('q', 'Q'):
            self.render_table_list()
            self._change_keybinds(self.keypress_default)
        elif key == 'd':
            self.render_table_desc()
            self._change_keybinds(self.keypress_in_table_desc)
        elif key == 'x':
            self.open_query_editor(query=self.session.default_query(),
                                   insert_top=True)
            return
        return self._common_keypresses(size, key, scrollable=True,
                                       focus_on_g=True, lr_pager=True)

    def keypress_in_table_desc(self, size, key):
        if key in ('q', 'Q'):
            if self.render_table_values():
                self._change_keybinds(self.keypress_in_table_session)
        return self._common_keypresses(size, key, focus_on_g=True)

    def keypress_in_editor(self, size, key):
        if key == 'ctrl x':
            self.execute_sql_in_query_editor()
        elif key == 'esc':
            self.query_editor = None
            self.render_table_list()
            self._change_keybinds(self.keypress_default)
        else:
            return super(MystiqueView, self).keypress(size, key)

    def keypress_in_query_result(self, size, key):
        if self.query_editor_is_shown:
            if key == 'esc':
                del self.listbox.body[0]
                return
            elif key == 'ctrl x':
                self.execute_sql_in_query_editor()
                Events.table_values_rendered.send(self)
            return self._common_keypresses(size, key, scrollable=True)
        if key == 'x':
            self.open_query_editor(query=self.session.default_query(),
                                   insert_top=True)
            return
        elif key == 'q':
            self.render_table_list()
        return self._common_keypresses(size, key, scrollable=True,
                                       focus_on_g=True, lr_pager=True)

    def _common_keypresses(self, size, key, focus_on_g=False, exit_on_q=False,
                           lr_pager=False, scrollable=False):
        if focus_on_g:
            if key == 'g':
                self.focus_to_top()
            elif key == 'G':
                self.focus_to_last()
        if exit_on_q and key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        if lr_pager:
            if key == 'k' and self._session.has_next:
                self._session.next_page()
                self.render_table_values()
            elif key == 'j' and self._session.has_prev():
                self._session.prev_page()
                self.render_table_values()
        if scrollable:
            if key in ('right', 'left'):
                ret = super(MystiqueView, self).keypress(size, key)

                focus_pos = self.listbox.focus_position
                fw = self.listbox.body[focus_pos]
                ow = get_original_widget(fw)

                if not isinstance(ow, TableColumn):
                    return ret

                focus = ow.get_focus_column()
                if focus > 1: # pos=0 is always urwid.Text (unfocusable)
                    for i, b in enumerate(self.listbox.body):
                        if i != focus_pos and \
                            isinstance(get_original_widget(b), TableColumn):
                                b.set_focus_column(focus)
                return ret

        return super(MystiqueView, self).keypress(size, key)

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
        self.footer_columns.clear_me()
        for cmd, desc in keybinds:
            self.footer_columns.widget_list.append(
                urwid.Columns([
                    ('fixed', len(cmd), txt(cmd)),
                    ('fixed', len(desc), urwid.AttrWrap(txt(desc), 'kb_desc_cmd'))
                ])
            )
        self.footer_columns.optimize_me()

    def _change_keybinds(self, handle_func):
        self._keypress_handler = handle_func
        Events.keybind_changed.send(view=self, name=handle_func.__name__)
        logger.info('keypress handler is updated: %s' % handle_func.__name__)

    @classmethod
    def _update_sizemap(cls, base_list, sizemap, max_len):
        for i, val in enumerate(base_list):
            size = len(val)
            if size > max_len:
                size = max_len
            if not sizemap.has_key(i) or sizemap[i] < size:
                sizemap[i] = size
        return sizemap

    @property
    def session(self):
        return self._session

    @property
    def query_editor_is_shown(self):
        return self.listbox.body[0] == self.query_editor

    @property
    def table_filter_is_shown(self):
        return self.listbox.body and \
            self.listbox.body[0] == self.table_filter


def info_of_session(view):
    view.update_information(str(view.session))


def info_of_table_desc(view):
    view.update_information('desc %s' % view.session.name())


def info_of_table_list(view):
    view.update_information('%s tables' % view.db_name)


def info_of_query_editor(view):
    view.update_information('query for %s' % view.db_name)


def keybind_information_in_footer(*args, **kwargs):
    view, name = (kwargs['view'], kwargs['name'])
    view.update_keybind_information(keybinds[name])


def main():
    logger.debug('Bootup mystique...')
    Events.query_editor_opened.connect(info_of_query_editor)
    Events.table_list_rendered.connect(info_of_table_list)
    Events.table_values_rendered.connect(info_of_session)
    Events.table_desc_rendered.connect(info_of_table_desc)
    Events.keybind_changed.connect(keybind_information_in_footer)
    view = MystiqueView(config.load_config())
    urwid.MainLoop(view, palette).run()


if __name__ == '__main__':
    main()

