# -*- coding: utf-8 -*-
#
# Copyright 2018 Thomas Bechtold <thomasbechtold@jpberlin.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# GNOME gobject introspection
import gi

gi.require_version('GExiv2', '0.10')
from gi.repository import GLib # noqa
from gi.repository import GExiv2 # noqa


def get_metadata(path):
    """
    get a gexiv2 metadata object or None for path
    :param path: path to an image that is supported by gexiv2
    :returns :py:class:`GExiv2.Metadata` or None
    """
    GExiv2.initialize()
    metadata = GExiv2.Metadata.new()
    try:
        metadata.open_path(path)
    except GLib.Error as e:
        print('{}: can not get metadata obj: {}'.format(path, e))
        return None
    else:
        return metadata
