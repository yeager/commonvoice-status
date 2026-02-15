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
    from gi.repository import Notify as _Notify
    HAS_NOTIFY = True
except (ValueError, ImportError):
    HAS_NOTIFY = False

from gi.repository import Gtk, Adw, Gio

from .window import CommonVoiceStatusWindow
from .i18n import init_i18n

_ = gettext.gettext



import json as _json
import platform as _platform
from pathlib import Path as _Path

_NOTIFY_APP = "commonvoice-status"


def _notify_config_path():
    return _Path(GLib.get_user_config_dir()) / _NOTIFY_APP / "notifications.json"


def _load_notify_config():
    try:
        return _json.loads(_notify_config_path().read_text())
    except Exception:
        return {"enabled": False}


def _save_notify_config(config):
    p = _notify_config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_json.dumps(config))


def _send_notification(summary, body="", icon="dialog-information"):
    if HAS_NOTIFY and _load_notify_config().get("enabled"):
        try:
            n = _Notify.Notification.new(summary, body, icon)
            n.show()
        except Exception:
            pass


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
