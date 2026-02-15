"""Main application window."""

import threading
import webbrowser

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk, GLib, Gio, Pango

from .api import fetch_languages, next_milestone
from .i18n import _


# Nordic + common comparison languages
DEFAULT_COMPARE = ["sv", "no", "da", "fi", "nb-NO", "nn-NO"]
DEFAULT_LOCALE = "sv-SE"

SORT_RECORDED = "recorded"
SORT_VALIDATED = "validated"
SORT_SPEAKERS = "speakers"


class CommonVoiceStatusWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_("Common Voice Status"))
        self.set_default_size(900, 700)

        self.languages = []
        self.selected_locale = DEFAULT_LOCALE
        self.sort_mode = SORT_VALIDATED

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # Header bar
        header = Adw.HeaderBar()

        # Refresh button
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text=_("Refresh"))
        refresh_btn.connect("clicked", self._on_refresh)
        header.pack_start(refresh_btn)

        # Sort menu
        sort_menu = Gio.Menu()
        sort_menu.append(_("Most validated hours"), "win.sort::validated")
        sort_menu.append(_("Most recorded hours"), "win.sort::recorded")
        sort_menu.append(_("Most speakers"), "win.sort::speakers")

        sort_btn = Gtk.MenuButton(icon_name="view-sort-descending-symbolic", menu_model=sort_menu, tooltip_text=_("Sort"))
        header.pack_end(sort_btn)

        # App menu
        app_menu = Gio.Menu()
        about_section = Gio.Menu()
        about_section.append(_("About"), "app.about")
        app_menu.append_section(None, about_section)
        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=app_menu)
        header.pack_end(menu_btn)

        sort_action = Gio.SimpleAction.new("sort", GLib.VariantType.new("s"))
        sort_action.connect("activate", self._on_sort_changed)
        self.add_action(sort_action)

        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(header)

        # Toolbar view
        toolbar = Adw.ToolbarView()

        # Content
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)

        # Loading spinner
        spinner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, spacing=12)
        spinner = Gtk.Spinner(spinning=True, width_request=32, height_request=32, halign=Gtk.Align.CENTER)
        spinner_box.append(spinner)
        spinner_box.append(Gtk.Label(label=_("Loading statistics…")))
        self.stack.add_named(spinner_box, "loading")

        # Error page
        self.error_status = Adw.StatusPage(
            icon_name="dialog-error-symbolic",
            title=_("Failed to load data"),
        )
        self.stack.add_named(self.error_status, "error")

        # Main content (scrolled)
        scrolled = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=16, margin_end=16, margin_top=8, margin_bottom=16, spacing=12)
        scrolled.set_child(Adw.Clamp(maximum_size=800, child=self.content_box))
        self.stack.add_named(scrolled, "content")

        main_box.append(self.stack)
        self.set_content(main_box)
        self.stack.set_visible_child_name("loading")

    def _load_data(self, force=False):
        self.stack.set_visible_child_name("loading")

        def worker():
            try:
                data = fetch_languages(force_refresh=force)
                GLib.idle_add(self._on_data_loaded, data)
            except Exception as e:
                GLib.idle_add(self._on_data_error, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_data_loaded(self, data):
        self.languages = data
        self._populate()
        self.stack.set_visible_child_name("content")

    def _on_data_error(self, message):
        self.error_status.set_description(message)
        self.stack.set_visible_child_name("error")

    def _on_refresh(self, btn):
        self._load_data(force=True)

    def _on_sort_changed(self, action, param):
        self.sort_mode = param.get_string()
        self._populate()

    def _sorted_languages(self):
        key_map = {
            SORT_VALIDATED: lambda l: l.get("validatedHours", 0),
            SORT_RECORDED: lambda l: l.get("recordedHours", 0),
            SORT_SPEAKERS: lambda l: l.get("speakersCount", 0),
        }
        return sorted(self.languages, key=key_map.get(self.sort_mode, key_map[SORT_VALIDATED]), reverse=True)

    def _populate(self):
        # Clear
        child = self.content_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.content_box.remove(child)
            child = next_child

        if not self.languages:
            return

        # Find selected language for feature card
        selected = None
        for lang in self.languages:
            if lang.get("locale") == self.selected_locale or lang.get("locale", "").startswith("sv"):
                selected = lang
                break
        if not selected:
            # fallback: first language
            selected = self.languages[0] if self.languages else None

        # Featured language card
        if selected:
            self._add_featured_card(selected)

        # Gap analysis
        if selected:
            self._add_gap_card(selected)

        # Comparison card (Nordic languages)
        self._add_comparison_card()

        # Full ranking
        self._add_ranking()

    def _add_featured_card(self, lang):
        group = Adw.PreferencesGroup(title=lang.get("english_name", lang.get("locale", "?")))

        rows = [
            (_("Recorded hours"), f"{lang.get('recordedHours', 0):,.0f}"),
            (_("Validated hours"), f"{lang.get('validatedHours', 0):,.0f}"),
            (_("Invalidated hours"), f"{lang.get('invalidatedHours', 0):,.1f}"),
            (_("Speakers"), f"{lang.get('speakersCount', 0):,}"),
            (_("Sentences"), f"{lang.get('sentencesCount', {}).get('currentCount', 0):,}"),
            (_("Locale"), lang.get("locale", "?")),
        ]
        for label, value in rows:
            row = Adw.ActionRow(title=label, subtitle=value)
            group.add(row)

        # Contribute button
        locale_code = lang.get("locale", "en")
        contribute_row = Adw.ActionRow(
            title=_("Contribute recordings"),
            subtitle=f"https://commonvoice.mozilla.org/{locale_code}",
            activatable=True,
        )
        contribute_row.add_suffix(Gtk.Image(icon_name="external-link-symbolic"))
        contribute_row.connect("activated", lambda r, lc=locale_code: webbrowser.open(f"https://commonvoice.mozilla.org/{lc}"))
        group.add(contribute_row)

        self.content_box.append(group)

    def _add_gap_card(self, lang):
        validated = lang.get("validatedHours", 0)
        milestone, remaining = next_milestone(validated)
        if milestone is None:
            return

        group = Adw.PreferencesGroup(title=_("Gap Analysis"))

        pct = (validated / milestone) * 100 if milestone else 100
        row = Adw.ActionRow(
            title=_("Next milestone: {} hours").format(f"{milestone:,}"),
            subtitle=_("{:.0f} hours remaining ({:.1f}% complete)").format(remaining, pct),
        )

        # Progress bar
        progress = Gtk.ProgressBar(fraction=pct / 100, valign=Gtk.Align.CENTER, hexpand=True)
        progress.set_size_request(150, -1)
        row.add_suffix(progress)
        group.add(row)

        self.content_box.append(group)

    def _add_comparison_card(self):
        group = Adw.PreferencesGroup(title=_("Nordic Comparison"))

        compare_locales = DEFAULT_COMPARE
        found = []
        for lang in self.languages:
            loc = lang.get("locale", "")
            if loc in compare_locales or loc.split("-")[0] in [c.split("-")[0] for c in compare_locales]:
                found.append(lang)

        found.sort(key=lambda l: l.get("validatedHours", 0), reverse=True)

        for lang in found:
            name = lang.get("english_name", lang.get("locale", "?"))
            validated = lang.get("validatedHours", 0)
            recorded = lang.get("recordedHours", 0)
            speakers = lang.get("speakersCount", 0)

            row = Adw.ActionRow(
                title=f"{name} ({lang.get('locale', '?')})",
                subtitle=_("{:.0f}h validated · {:.0f}h recorded · {:,} speakers").format(validated, recorded, speakers),
            )
            group.add(row)

        if not found:
            row = Adw.ActionRow(title=_("No Nordic languages found"))
            group.add(row)

        self.content_box.append(group)

    def _add_ranking(self):
        group = Adw.PreferencesGroup(title=_("All Languages"))
        group.set_description(
            {
                SORT_VALIDATED: _("Sorted by validated hours"),
                SORT_RECORDED: _("Sorted by recorded hours"),
                SORT_SPEAKERS: _("Sorted by speakers"),
            }.get(self.sort_mode, "")
        )

        sorted_langs = self._sorted_languages()
        for i, lang in enumerate(sorted_langs[:50], 1):
            name = lang.get("english_name", lang.get("locale", "?"))
            validated = lang.get("validatedHours", 0)
            recorded = lang.get("recordedHours", 0)
            speakers = lang.get("speakersCount", 0)

            row = Adw.ActionRow(
                title=f"#{i}  {name}",
                subtitle=_("{:.0f}h validated · {:.0f}h recorded · {:,} speakers").format(validated, recorded, speakers),
            )
            group.add(row)

        self.content_box.append(group)
