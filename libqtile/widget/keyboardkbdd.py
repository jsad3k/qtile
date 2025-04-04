# Copyright (c) 2015 Ali Mousavi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# type: ignore

import re

from libqtile.log_utils import logger
from libqtile.utils import add_signal_receiver
from libqtile.widget import base


class KeyboardKbdd(base.ThreadPoolText):
    """Widget for changing keyboard layouts per window, using kbdd

    kbdd should be installed and running, you can get it from:
    https://github.com/qnikst/kbdd

    The widget also requires dbus-fast_.

    .. _dbus-fast: https://pypi.org/project/dbus-fast/
    """

    defaults = [
        ("update_interval", 1, "Update interval in seconds."),
        (
            "configured_keyboards",
            ["us", "ir"],
            "your predefined list of keyboard layouts.example: ['us', 'ir', 'es']",
        ),
        (
            "colours",
            None,
            "foreground colour for each layout"
            "either 'None' or a list of colours."
            "example: ['ffffff', 'E6F0AF']. ",
        ),
    ]

    def __init__(self, **config):
        base.ThreadPoolText.__init__(self, "", **config)
        self.add_defaults(KeyboardKbdd.defaults)
        self.keyboard = self.configured_keyboards[0]
        self.is_kbdd_running = self._check_kbdd()
        if not self.is_kbdd_running:
            self.keyboard = "N/A"

    def _check_kbdd(self):
        try:
            running_list = self.call_process(["ps", "axw"])
        except FileNotFoundError:
            logger.error("'ps' is not installed. Cannot check if kbdd is running.")
            return False

        if re.search("kbdd", running_list):
            self.keyboard = self.configured_keyboards[0]
            return True

        logger.error("kbdd is not running.")
        return False

    async def _config_async(self):
        subscribed = await add_signal_receiver(
            self._signal_received,
            session_bus=True,
            signal_name="layoutChanged",
            dbus_interface="ru.gentoo.kbdd",
        )

        if not subscribed:
            logger.warning("Could not subscribe to kbdd signal.")

    def _signal_received(self, message):
        self._layout_changed(*message.body)

    def _layout_changed(self, layout_changed):
        """
        Handler for "layoutChanged" dbus signal.
        """
        if self.colours:
            self._set_colour(layout_changed)
        self.keyboard = self.configured_keyboards[layout_changed]

    def _set_colour(self, index):
        if isinstance(self.colours, list):
            try:
                self.layout.colour = self.colours[index]
            except IndexError:
                self._set_colour(index - 1)
        else:
            logger.error(
                'variable "colours" should be a list, to set a\
                            colour for all layouts, use "foreground".'
            )

    def poll(self):
        if not self.is_kbdd_running:
            if self._check_kbdd():
                self.is_kbdd_running = True
                return self.configured_keyboards[0]
        return self.keyboard
