"""Main application window."""

import csv
import json
import threading
import webbrowser

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk, GLib, Gio, Pango, Gdk

from .api import fetch_languages, next_milestone
from .main import _send_notification
from .i18n import _


# Nordic + common comparison languages
DEFAULT_COMPARE = ["sv", "no", "da", "fi", "nb-NO", "nn-NO"]
DEFAULT_LOCALE = "sv-SE"

# Milestones for validated hours coloring
_CV_MILESTONES = [10, 50, 100, 500, 1000, 5000]


def _setup_heatmap_css():
    css = b"""
    .heatmap-green { background-color: #26a269; color: white; border-radius: 8px; }
    .heatmap-yellow { background-color: #e5a50a; color: white; border-radius: 8px; }
    .heatmap-orange { background-color: #ff7800; color: white; border-radius: 8px; }
    .heatmap-red { background-color: #c01c28; color: white; border-radius: 8px; }
    .heatmap-gray { background-color: #77767b; color: white; border-radius: 8px; }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def _cv_heatmap_class(validated_hours):
    """Color based on validated hours thresholds."""
    if validated_hours >= 500:
        return "heatmap-green"
    elif validated_hours >= 100:
        return "heatmap-yellow"
    elif validated_hours >= 10:
        return "heatmap-orange"
    elif validated_hours > 0:
        return "heatmap-red"
    return "heatmap-gray"

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

        _setup_heatmap_css()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # Header bar
        header = Adw.HeaderBar()

        # Refresh button
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text=_("Refresh"))
        refresh_btn.connect("clicked", self._on_refresh)
        header.pack_start(refresh_btn)

        # Export button
        export_btn = Gtk.Button(icon_name="document-save-symbolic", tooltip_text=_("Export data"))
        export_btn.connect("clicked", self._on_export_clicked)
        header.pack_end(export_btn)

        # Sort menu
        sort_menu = Gio.Menu()
        sort_menu.append(_("Most validated hours"), "win.sort::validated")
        sort_menu.append(_("Most recorded hours"), "win.sort::recorded")
        sort_menu.append(_("Most speakers"), "win.sort::speakers")

        sort_btn = Gtk.MenuButton(icon_name="view-sort-descending-symbolic", menu_model=sort_menu, tooltip_text=_("Sort"))
        header.pack_end(sort_btn)

        # Theme toggle
        self._theme_btn = Gtk.Button(icon_name="weather-clear-night-symbolic",
                                     tooltip_text="Toggle dark/light theme")
        self._theme_btn.connect("clicked", self._on_theme_toggle)
        header.pack_end(self._theme_btn)

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

        # Status bar
        self._status_bar = Gtk.Label(label="", halign=Gtk.Align.START,
                                     margin_start=12, margin_end=12, margin_bottom=4)
        self._status_bar.add_css_class("dim-label")
        self._status_bar.add_css_class("caption")
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
        self._update_status_bar()


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

    def _on_export_clicked(self, *_args):
        dialog = Adw.MessageDialog(transient_for=self,
                                   heading=_("Export Data"),
                                   body=_("Choose export format:"))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("csv", "CSV")
        dialog.add_response("json", "JSON")
        dialog.set_response_appearance("csv", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_export_format_chosen)
        dialog.present()

    def _on_export_format_chosen(self, dialog, response):
        if response not in ("csv", "json"):
            return
        self._export_fmt = response
        fd = Gtk.FileDialog()
        fd.set_initial_name(f"commonvoice-stats.{response}")
        fd.save(self, None, self._on_export_save)

    def _on_export_save(self, dialog, result):
        try:
            path = dialog.save_finish(result).get_path()
        except Exception:
            return
        data = [{"locale": l.get("locale", ""), "name": l.get("english_name", ""),
                 "recorded_hours": l.get("recordedHours", 0),
                 "validated_hours": l.get("validatedHours", 0),
                 "invalidated_hours": l.get("invalidatedHours", 0),
                 "speakers": l.get("speakersCount", 0)}
                for l in self.languages]
        if not data:
            return
        if self._export_fmt == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=data[0].keys())
                w.writeheader()
                w.writerows(data)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

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
        # Heatmap grid for Nordic comparison
        label = Gtk.Label(label=_("Nordic Comparison"), xalign=0)
        label.add_css_class("title-2")
        label.set_margin_top(8)
        self.content_box.append(label)

        compare_locales = DEFAULT_COMPARE
        found = []
        for lang in self.languages:
            loc = lang.get("locale", "")
            if loc in compare_locales or loc.split("-")[0] in [c.split("-")[0] for c in compare_locales]:
                found.append(lang)

        found.sort(key=lambda l: l.get("validatedHours", 0), reverse=True)

        if found:
            flow = Gtk.FlowBox()
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_homogeneous(True)
            flow.set_min_children_per_line(2)
            flow.set_max_children_per_line(6)
            flow.set_column_spacing(6)
            flow.set_row_spacing(6)
            flow.set_margin_top(8)
            flow.set_margin_bottom(8)

            for lang in found:
                name = lang.get("english_name", lang.get("locale", "?"))
                validated = lang.get("validatedHours", 0)
                recorded = lang.get("recordedHours", 0)
                speakers = lang.get("speakersCount", 0)

                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                box.set_size_request(150, 80)
                box.add_css_class(_cv_heatmap_class(validated))
                box.set_margin_start(4)
                box.set_margin_end(4)
                box.set_margin_top(4)
                box.set_margin_bottom(4)

                name_lbl = Gtk.Label(label=name)
                name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                name_lbl.set_margin_top(8)
                name_lbl.set_margin_start(6)
                name_lbl.set_margin_end(6)
                box.append(name_lbl)

                val_lbl = Gtk.Label(label=f"{validated:.0f}h validated")
                box.append(val_lbl)

                spk_lbl = Gtk.Label(label=f"{speakers:,} speakers")
                spk_lbl.set_margin_bottom(6)
                box.append(spk_lbl)

                box.set_tooltip_text(f"{name}: {recorded:.0f}h recorded, {validated:.0f}h validated")
                locale_code = lang.get("locale", "en")
                gesture = Gtk.GestureClick()
                gesture.connect("released", lambda g, n, x, y, lc=locale_code: webbrowser.open(f"https://commonvoice.mozilla.org/{lc}"))
                box.add_controller(gesture)
                box.set_cursor(Gdk.Cursor.new_from_name("pointer"))

                flow.append(box)

            self.content_box.append(flow)
        else:
            no_data = Gtk.Label(label=_("No Nordic languages found"))
            no_data.add_css_class("dim-label")
            self.content_box.append(no_data)

    def _add_ranking(self):
        sort_desc = {
            SORT_VALIDATED: _("Sorted by validated hours"),
            SORT_RECORDED: _("Sorted by recorded hours"),
            SORT_SPEAKERS: _("Sorted by speakers"),
        }.get(self.sort_mode, "")

        label = Gtk.Label(label=_("All Languages") + f" — {sort_desc}", xalign=0)
        label.add_css_class("title-2")
        label.set_margin_top(12)
        self.content_box.append(label)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_min_children_per_line(3)
        flow.set_max_children_per_line(8)
        flow.set_column_spacing(4)
        flow.set_row_spacing(4)
        flow.set_margin_top(8)
        flow.set_margin_bottom(8)

        sorted_langs = self._sorted_languages()
        for i, lang in enumerate(sorted_langs[:50], 1):
            name = lang.get("english_name", lang.get("locale", "?"))
            validated = lang.get("validatedHours", 0)
            recorded = lang.get("recordedHours", 0)

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            box.set_size_request(130, 60)
            box.add_css_class(_cv_heatmap_class(validated))
            box.set_margin_start(3)
            box.set_margin_end(3)
            box.set_margin_top(3)
            box.set_margin_bottom(3)

            name_lbl = Gtk.Label(label=f"#{i} {name}")
            name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            name_lbl.set_max_width_chars(16)
            name_lbl.set_margin_top(6)
            name_lbl.set_margin_start(4)
            name_lbl.set_margin_end(4)
            box.append(name_lbl)

            val_lbl = Gtk.Label(label=f"{validated:.0f}h")
            val_lbl.set_margin_bottom(6)
            box.append(val_lbl)

            box.set_tooltip_text(f"{name}: {validated:.0f}h validated, {recorded:.0f}h recorded")
            locale_code = lang.get("locale", "en")
            gesture = Gtk.GestureClick()
            gesture.connect("released", lambda g, n, x, y, lc=locale_code: webbrowser.open(f"https://commonvoice.mozilla.org/{lc}"))
            box.add_controller(gesture)
            box.set_cursor(Gdk.Cursor.new_from_name("pointer"))

            flow.append(box)

        self.content_box.append(flow)

    def _on_theme_toggle(self, _btn):
        sm = Adw.StyleManager.get_default()
        if sm.get_color_scheme() == Adw.ColorScheme.FORCE_DARK:
            sm.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            self._theme_btn.set_icon_name("weather-clear-night-symbolic")
        else:
            sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            self._theme_btn.set_icon_name("weather-clear-symbolic")

    def _update_status_bar(self):
        self._status_bar.set_text("Last updated: " + _dt_now.now().strftime("%Y-%m-%d %H:%M"))
