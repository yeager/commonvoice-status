"""Desktop notification helper."""

import json as _json
from pathlib import Path as _Path

try:
    import gi
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify as _Notify
    HAS_NOTIFY = True
except (ValueError, ImportError):
    HAS_NOTIFY = False
    _Notify = None


def _notify_config_path():
    return _Path.home() / ".config" / "commonvoice-status" / "notifications.json"


def _load_notify_config():
    p = _notify_config_path()
    if p.exists():
        try:
            return _json.loads(p.read_text())
        except Exception:
            pass
    return {"enabled": True}


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
