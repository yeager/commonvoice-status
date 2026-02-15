#!/usr/bin/env python3
"""Common Voice Status — GTK4/Adwaita app for viewing Mozilla Common Voice statistics."""

import gettext
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio

from .window import CommonVoiceStatusWindow
from .i18n import init_i18n

_ = gettext.gettext


class CommonVoiceStatusApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="se.danielnylander.CommonVoiceStatus",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = CommonVoiceStatusWindow(application=self)
        win.present()

    def _on_about(self, *_args):
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name=_("Common Voice Status"),
            application_icon="commonvoice-status",
            version="0.1.1",
            developer_name="Daniel Nylander",
            developers=["Daniel Nylander <daniel@danielnylander.se>"],
            copyright="© 2026 Daniel Nylander",
            license_type=Gtk.License.GPL_3_0,
            website="https://github.com/yeager/commonvoice-status",
            issue_url="https://github.com/yeager/commonvoice-status/issues",
            translate_url="https://app.transifex.com/danielnylander/commonvoice-status/",
            translator_credits="Daniel Nylander <daniel@danielnylander.se>",
            comments=_("View Mozilla Common Voice statistics per language"),
        )
        about.present()


def main():
    init_i18n()
    app = CommonVoiceStatusApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
