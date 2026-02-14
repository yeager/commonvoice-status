#!/usr/bin/env python3
"""Common Voice Status — GTK4/Adwaita app for viewing Mozilla Common Voice statistics."""

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio

from .window import CommonVoiceStatusWindow
from .i18n import init_i18n


class CommonVoiceStatusApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="se.danielnylander.CommonVoiceStatus",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = CommonVoiceStatusWindow(application=self)
        win.present()


def main():
    init_i18n()
    app = CommonVoiceStatusApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
