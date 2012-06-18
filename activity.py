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
#from gettext import gettext as _
import gettext

import gtk
import gobject
import gconf

from sugar.activity import activity
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.activity.widgets import ActivityToolbarButton
from sugar.activity.widgets import StopButton
from sugar.graphics import style
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.icon import Icon

DEFAULT_CHANGE_IMAGE_TIME = 10
POWERD_INHIBIT_DIR = '/var/run/powerd-inhibit-suspend'


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
        prev_bt.connect("clicked", self.image_viewer.prev_image_clicked_cb,
                None)
        toolbar_box.toolbar.insert(prev_bt, -1)

        next_bt = ToolButton("go-next-paired")
        next_bt.connect("clicked", self.image_viewer.next_image_clicked_cb,
                None)
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

    def can_close(self):
        self.image_viewer.finish()
        return True


class CustomButton(gtk.EventBox):

    def __init__(self, icon, size):
        super(gtk.EventBox, self).__init__()
        image = gtk.Image()
        path = os.path.expanduser('~/Activities/Welcome.activity/icons/')
        pxb = gtk.gdk.pixbuf_new_from_file_at_size('%s/%s.svg' % (path, icon),
                size, size)
        image.set_from_pixbuf(pxb)
        self.add(image)
        self.modify_bg(gtk.STATE_NORMAL, style.COLOR_WHITE.get_gdk_color())


class ImageCollectionViewer(gtk.VBox):

    __gtype_name__ = 'WelcomeDialog'

    def __init__(self, start_window=True):
        super(gtk.VBox, self).__init__()
        self.using_powerd = self._verify_powerd_directory()
        self._inhibit_suspend()

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

            # init gettext
            locale_path = \
                    os.path.expanduser('~/Activities/Welcome.activity/locale/')
            gettext.bindtextdomain('org.laptop.WelcomeActivity', locale_path)
            gettext.textdomain('org.laptop.WelcomeActivity')
            _ = gettext.gettext

            _next_button = gtk.Button()
            _next_button.set_label(_('Next'))
            next_image = Icon(icon_name='go-right')
            _next_button.set_image(next_image)
            _next_button.connect('clicked', self.__next_clicked_cb)
            right_box.pack_end(_next_button, False, False,
                    padding=style.zoom(30))
            bt_width, bt_height = _next_button.size_request()

            prev_bt = CustomButton('go-previous-paired-grey', bt_height)
            center_box.pack_start(prev_bt, False, False, 5)
            prev_bt.connect('button-press-event', self.prev_image_clicked_cb)

            next_bt = CustomButton('go-next-paired-grey', bt_height)
            center_box.pack_start(next_bt, False, False, 5)
            next_bt.connect('button-press-event', self.next_image_clicked_cb)

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
        self._allow_suspend()
        gtk.main_quit()

    def auto_change_image(self):
        self.next_image_clicked_cb(None, None)
        self.timer_id = gobject.timeout_add_seconds(DEFAULT_CHANGE_IMAGE_TIME,
                self.auto_change_image)
        return True

    def next_image_clicked_cb(self, button, event):
        gobject.source_remove(self.timer_id)
        self.image_order += 1
        if self.image_order == len(self.image_files_list):
            self.image_order = 0
        self.image.set_from_file(self.image_files_list[self.image_order])

    def prev_image_clicked_cb(self, button, event):
        gobject.source_remove(self.timer_id)
        self.image_order -= 1
        if self.image_order < 0:
            self.image_order = len(self.image_files_list) - 1
        self.image.set_from_file(self.image_files_list[self.image_order])

    def finish(self):
        self._allow_suspend()

    def _verify_powerd_directory(self):
        using_powerd = os.access(POWERD_INHIBIT_DIR, os.W_OK)
        logging.debug("using_powerd: %d", using_powerd)
        return using_powerd

    def _inhibit_suspend(self):
        if self.using_powerd:
            flag_file_name = self._powerd_flag_name()
            try:
                file(flag_file_name, 'w').write('')
                logging.debug("inhibit_suspend file is %s", flag_file_name)
            except IOError:
                pass

    def _allow_suspend(self):
        if self.using_powerd:
            flag_file_name = self._powerd_flag_name()
            try:
                os.unlink(flag_file_name)
                logging.debug("allow_suspend unlinking %s", flag_file_name)
            except IOError:
                pass

    def _powerd_flag_name(self):
        return POWERD_INHIBIT_DIR + "/%u" % os.getpid()


def set_fonts():
    client = gconf.client_get_default()
    face = client.get_string('/desktop/sugar/font/default_face')
    size = client.get_float('/desktop/sugar/font/default_size')
    settings = gtk.settings_get_default()
    settings.set_property("gtk-font-name", "%s %f" % (face, size))


def main():
    set_fonts()
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
