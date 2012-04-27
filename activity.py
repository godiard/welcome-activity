# Copyright 2012 One Laptop per Child
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import logging
from gettext import gettext as _

import gtk
import gobject

from sugar.activity import activity
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.activity.widgets import ActivityButton
from sugar.activity.widgets import TitleEntry
from sugar.activity.widgets import StopButton
from sugar.activity.widgets import ShareButton
from sugar.graphics import style
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.icon import Icon


class WelcomeActivity(activity.Activity):
    """WelcomeActivity class as specified in activity.info"""

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        # we do not have collaboration features
        # make the share option insensitive
        self.max_participants = 1

        # toolbar with the new toolbar redesign
        toolbar_box = ToolbarBox()

        activity_button = ActivityButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        title_entry = TitleEntry(self)
        toolbar_box.toolbar.insert(title_entry, -1)
        title_entry.show()

        share_button = ShareButton(self)
        toolbar_box.toolbar.insert(share_button, -1)
        share_button.show()

        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        label = gtk.Label("")
        label.show()
        self.set_canvas(label)
        gobject.idle_add(self.show_dialog)

    def show_dialog(self):
        welcome_dialog = WelcomeDialog()
        welcome_dialog.set_transient_for(self.get_toplevel())


class _DialogWindow(gtk.Window):

    # A base class for a modal dialog window.

    def __init__(self, icon_name, title):
        super(_DialogWindow, self).__init__()

        self.set_border_width(style.LINE_WIDTH)
        offset = style.GRID_CELL_SIZE
        width = gtk.gdk.screen_width() - style.GRID_CELL_SIZE * 2
        height = gtk.gdk.screen_height() - style.GRID_CELL_SIZE * 2
        self.set_size_request(width, height)
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.set_decorated(False)
        self.set_border_width(style.LINE_WIDTH)
        self.set_resizable(False)
        self.set_modal(True)
        self.modify_bg(gtk.STATE_NORMAL, style.COLOR_WHITE.get_gdk_color())

        vbox = gtk.VBox()
        self.add(vbox)

        toolbar = _DialogToolbar(icon_name, title)
        toolbar.connect('stop-clicked', self._stop_clicked_cb)
        vbox.pack_start(toolbar, False)

        self.content_vbox = gtk.VBox()
        self.content_vbox.set_border_width(1)
        vbox.add(self.content_vbox)

        self.connect('realize', self._realize_cb)

    def _stop_clicked_cb(self, source):
        self.destroy()

    def _realize_cb(self, source):
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.window.set_accept_focus(True)


class _DialogToolbar(gtk.Toolbar):

    # Displays a dialog window's toolbar, with title, icon, and close box.

    __gsignals__ = {
        'stop-clicked': (gobject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, icon_name, title):
        super(_DialogToolbar, self).__init__()

        if icon_name is not None:
            icon = Icon()
            icon.set_from_icon_name(icon_name, gtk.ICON_SIZE_LARGE_TOOLBAR)
            self._add_widget(icon)

        self._add_separator()

        label = gtk.Label(title)
        self._add_widget(label)

        self._add_separator(expand=True)

        stop = ToolButton(icon_name='dialog-cancel')
        stop.set_tooltip(_('Done'))
        stop.connect('clicked', self._stop_clicked_cb)
        self.add(stop)

    def _add_separator(self, expand=False):
        separator = gtk.SeparatorToolItem()
        separator.set_expand(expand)
        separator.set_draw(False)
        self.add(separator)

    def _add_widget(self, widget):
        tool_item = gtk.ToolItem()
        tool_item.add(widget)
        self.add(tool_item)

    def _stop_clicked_cb(self, button):
        self.emit('stop-clicked')


class WelcomeDialog(_DialogWindow):

    __gtype_name__ = 'WelcomeDialog'

    def __init__(self):

        # TODO: May be remove the title
        super(WelcomeDialog, self).__init__(None, _('Welcome'))

        self.image = gtk.Image()
        self.content_vbox.pack_start(self.image, True, True, padding=0)

        bottom_toolbar = gtk.Toolbar()
        self.content_vbox.pack_start(bottom_toolbar, False, padding=0)

        images_path = os.path.expanduser('~/Activities/Welcome.activity/images/')

        self.image_order = 0
        self.image_files_list = []
        for fname in os.listdir(images_path):
            self.image_files_list.append(images_path + fname)
            logging.error('Image file: %s', fname)

        if self.image_files_list:
            self.image.set_from_file(self.image_files_list[self.image_order])

        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        bottom_toolbar.insert(separator, -1)

        prev_bt = ToolButton(icon_name='go-previous')
        bottom_toolbar.insert(prev_bt, -1)
        prev_bt.connect('clicked', self.__prev_clicked_cb)

        next_bt = ToolButton(icon_name='go-next')
        bottom_toolbar.insert(next_bt, -1)
        next_bt.connect('clicked', self.__next_clicked_cb)
        self.show_all()

        width, height = self.image.size_request()

        height_av = gtk.gdk.screen_height() - style.GRID_CELL_SIZE * 4
        width_av = gtk.gdk.screen_width() - style.GRID_CELL_SIZE * 2
        size_label = gtk.Label('  Size available for image: %d x %d' %
                (width_av, height_av))
        item = gtk.ToolItem()
        item.add(size_label)
        bottom_toolbar.insert(item, 0)
        item.show_all()

    def __next_clicked_cb(self, button):
        self.image_order += 1
        if self.image_order == len(self.image_files_list):
            self.image_order = 0
        self.image.set_from_file(self.image_files_list[self.image_order])

    def __prev_clicked_cb(self, button):
        self.image_order -= 1
        if self.image_order < 0:
            self.image_order = len(self.image_files_list) - 1
        self.image.set_from_file(self.image_files_list[self.image_order])


def main():
    welcome_dialog = WelcomeDialog()
    #welcome_dialog.set_transient_for(self.get_toplevel())
    welcome_dialog.connect("destroy", gtk.main_quit)
    gtk.main()

if __name__ == "__main__":
    main()
