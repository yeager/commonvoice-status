#!/usr/bin/env python3
"""Common Voice Status — GTK4/Adwaita app for viewing Mozilla Common Voice statistics."""

import gettext
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
# Optional desktop notifications
try:
    gi.require_version("Notify", "0.7")
    from gi.repository import Gtk, Notify as _Notify
    HAS_NOTIFY = True
except (ValueError, ImportError):
    HAS_NOTIFY = False

from gi.repository import Gtk, Adw, Gio

from .notify import _send_notification, _load_notify_config, _save_notify_config
from .window import CommonVoiceStatusWindow
from .i18n import init_i18n

_ = gettext.gettext

import json as _json
import platform as _platform
from pathlib import Path as _Path

_NOTIFY_APP = "commonvoice-status"

def _get_system_info():
    return "\n".join([
        f"App: Common Voice Status",
        f"Version: {"0.1.1"}",
        f"GTK: {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}",
        f"Adw: {Adw.get_major_version()}.{Adw.get_minor_version()}.{Adw.get_micro_version()}",
        f"Python: {_platform.python_version()}",
        f"OS: {_platform.system()} {_platform.release()} ({_platform.machine()})",
    ])

class CommonVoiceStatusApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="se.danielnylander.CommonVoiceStatus",
        GLib.set_application_name(_("Common Voice Status"))
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        if HAS_NOTIFY:
            _Notify.init("commonvoice-status")
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

        export_action = Gio.SimpleAction.new("export", None)
        export_action.connect("activate", lambda *_: self.props.active_window and self.props.active_window._on_export_clicked())
        self.add_action(export_action)
        self.set_accels_for_action("app.export", ["<Control>e"])

        notif_action = Gio.SimpleAction.new("toggle-notifications", None)
        notif_action.connect("activate", lambda *_: _save_notify_config({"enabled": not _load_notify_config().get("enabled", False)}))
        self.add_action(notif_action)

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.set_accels_for_action("app.quit", ["<Control>q"])
        self.set_accels_for_action("app.refresh", ["F5"])
        self.set_accels_for_action("app.shortcuts", ["<Control>slash"])
        for n, cb in [("quit", lambda *_: self.quit()),
                      ("refresh", lambda *_: self._do_refresh()),
                      ("shortcuts", self._show_shortcuts_window)]:
            a = Gio.SimpleAction.new(n, None); a.connect("activate", cb); self.add_action(a)

    def _do_refresh(self):
        w = self.get_active_window()
        if w and hasattr(w, '_load_data'): w._load_data(force=True)
        elif w and hasattr(w, '_on_refresh'): w._on_refresh(None)

    def _show_shortcuts_window(self, *_args):
        win = Gtk.ShortcutsWindow(transient_for=self.get_active_window(), modal=True)
        section = Gtk.ShortcutsSection(visible=True, max_height=10)
        group = Gtk.ShortcutsGroup(visible=True, title="General")
        for accel, title in [("<Control>q", "Quit"), ("F5", "Refresh"), ("<Control>slash", "Keyboard shortcuts")]:
            s = Gtk.ShortcutsShortcut(visible=True, accelerator=accel, title=title)
            group.append(s)
        section.append(group)
        win.add_child(section)
        win.present()

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = CommonVoiceStatusWindow(application=self)
        win.present()

    def _on_about(self, *_args):
        about = Adw.AboutDialog(
            application_name=_("Common Voice Status"),
            application_icon="commonvoice-status",
            version="0.1.1",
            developer_name="Daniel Nylander",
            developers=["Daniel Nylander <daniel@danielnylander.se>"],
            copyright="© 2026 Daniel Nylander",
            license_type=Gtk.License.GPL_3_0,
            website="https://github.com/yeager/commonvoice-status",
            issue_url="https://github.com/yeager/commonvoice-status/issues",
            translator_credits=_("Translate this app: https://www.transifex.com/danielnylander/commonvoice-status/"),
            comments=_("View Mozilla Common Voice statistics per language"),
        )
        about.set_debug_info(_get_system_info())
        about.set_debug_info_filename("commonvoice-status-debug.txt")
        about.add_link(_("Help translate"), "https://app.transifex.com/danielnylander/commonvoice-status/")

        about.present(self.props.active_window)

def main():
    init_i18n()
    app = CommonVoiceStatusApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    sys.exit(main())
