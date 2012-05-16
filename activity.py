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
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.graphics import style
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.icon import Icon

DEFAULT_CHANGE_IMAGE_TIME = 10


class WelcomeActivity(activity.Activity):
    """WelcomeActivity class as specified in activity.info"""

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        # we do not have collaboration features
        # make the share option insensitive
        self.max_participants = 1

        # toolbar with the new toolbar redesign
        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)

        toolbar_box.toolbar.insert(gtk.SeparatorToolItem(), -1)

        self.image_viewer = ImageCollectionViewer(False)

        prev_bt = ToolButton("go-previous-paired")
        prev_bt.connect("clicked", self.image_viewer.prev_image_clicked_cb)
        toolbar_box.toolbar.insert(prev_bt, -1)

        next_bt = ToolButton("go-next-paired")
        next_bt.connect("clicked", self.image_viewer.next_image_clicked_cb)
        toolbar_box.toolbar.insert(next_bt, -1)

        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show_all()

        self.modify_bg(gtk.STATE_NORMAL, style.COLOR_WHITE.get_gdk_color())
        self.set_canvas(self.image_viewer)


class CustomButton(gtk.Button):

    def __init__(self, icon):
        super(gtk.Button, self).__init__()
        path = os.path.expanduser('~/Activities/Welcome.activity/icons/')
        icon = Icon(file='%s/%s.svg' % (path, icon))
        self.set_image(icon)
        self.modify_bg(gtk.STATE_NORMAL, style.COLOR_WHITE.get_gdk_color())
        self.modify_bg(gtk.STATE_PRELIGHT, style.COLOR_WHITE.get_gdk_color())


class ImageCollectionViewer(gtk.VBox):

    __gtype_name__ = 'WelcomeDialog'

    def __init__(self, start_window=True):
        super(gtk.VBox, self).__init__()

        self.image = gtk.Image()
        self.pack_start(self.image, True, True, padding=0)

        # images management
        images_path = \
                os.path.expanduser('~/Activities/Welcome.activity/images/')

        self.image_order = 0
        self.image_files_list = []
        for fname in os.listdir(images_path):
            self.image_files_list.append(images_path + fname)
            logging.error('Image file: %s', fname)

        if self.image_files_list:
            self.image.set_from_file(self.image_files_list[self.image_order])

        if start_window:
            # Create bottom controls

            bottom_toolbar = gtk.HBox()
            self.pack_start(bottom_toolbar, False, padding=style.zoom(30))

            left_box = gtk.HBox()
            bottom_toolbar.pack_start(left_box, False, padding=0)

            center_align = gtk.Alignment(0.5, 0, 0, 0)
            center_box = gtk.HBox()
            center_align.add(center_box)
            bottom_toolbar.pack_start(center_align, True, True, padding=0)

            right_box = gtk.HBox()
            bottom_toolbar.pack_start(right_box, False, padding=0)

            prev_bt = CustomButton('go-previous-paired-grey')
            center_box.pack_start(prev_bt, False, False)
            prev_bt.connect('clicked', self.prev_image_clicked_cb)

            next_bt = CustomButton('go-next-paired-grey')
            center_box.pack_start(next_bt, False, False)
            next_bt.connect('clicked', self.next_image_clicked_cb)

            _next_button = gtk.Button()
            _next_button.set_label(gtk.STOCK_GO_FORWARD)
            _next_button.set_use_stock(True)
            _next_button.connect('clicked', self.__next_clicked_cb)
            right_box.pack_end(_next_button, False, False,
                    padding=style.zoom(30))

            # do the right_box and left_box have the same size
            width = int(gtk.gdk.screen_width() / 4)
            right_box.set_size_request(width, -1)
            left_box.set_size_request(width, -1)

        self.show_all()

        self.timer_id = gobject.timeout_add_seconds(DEFAULT_CHANGE_IMAGE_TIME,
                self.auto_change_image)

        # calculate space available for images
        #   (only to tell to the designers)
        height_av = gtk.gdk.screen_height() - style.GRID_CELL_SIZE * 2
        width_av = gtk.gdk.screen_width()
        print 'Size available for image: %d x %d' % (width_av, height_av)

    def __next_clicked_cb(self, button):
        gtk.main_quit()

    def auto_change_image(self):
        self.next_image_clicked_cb(None)
        return True

    def next_image_clicked_cb(self, button):
        gobject.source_remove(self.timer_id)
        self.timer_id = gobject.timeout_add_seconds(DEFAULT_CHANGE_IMAGE_TIME,
                self.auto_change_image)
        self.image_order += 1
        if self.image_order == len(self.image_files_list):
            self.image_order = 0
        self.image.set_from_file(self.image_files_list[self.image_order])

    def prev_image_clicked_cb(self, button):
        self.image_order -= 1
        if self.image_order < 0:
            self.image_order = len(self.image_files_list) - 1
        self.image.set_from_file(self.image_files_list[self.image_order])


def main():
    win = gtk.Window()
    image_viewer = ImageCollectionViewer()
    win.add(image_viewer)
    win.set_size_request(gtk.gdk.screen_width(), gtk.gdk.screen_height())
    win.set_position(gtk.WIN_POS_CENTER_ALWAYS)
    win.set_decorated(False)
    win.modify_bg(gtk.STATE_NORMAL, style.COLOR_WHITE.get_gdk_color())

    win.show_all()
    win.connect("destroy", gtk.main_quit)
    gtk.main()

if __name__ == "__main__":
    main()
