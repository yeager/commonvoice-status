"""Internationalization support."""

import gettext
import locale
import os

APP_NAME = "commonvoice-status"
LOCALE_DIR = None  # Will be set during init


def init_i18n():
    global LOCALE_DIR
    # Check local dev path first, then system
    local_path = os.path.join(os.path.dirname(__file__), "..", "..", "po", "locale")
    if os.path.isdir(local_path):
        LOCALE_DIR = local_path
    else:
        LOCALE_DIR = "/usr/share/locale"

    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass

    gettext.bindtextdomain(APP_NAME, LOCALE_DIR)
    gettext.textdomain(APP_NAME)


def _(message):
    return gettext.gettext(message)
