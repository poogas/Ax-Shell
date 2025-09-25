import gi
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.stack import Stack

import config.data as data

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

import modules.icons as icons
from modules.kanban import Kanban
from modules.mixer import Mixer
from modules.pins import Pins
from modules.wallpapers import WallpaperSelector
from modules.widgets import Widgets


class Dashboard(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="dashboard",
            orientation="v",
            spacing=8,
            h_align="center",
            v_align="center",
            h_expand=True,
            visible=True,
            all_visible=True,
        )

        self.notch = kwargs["notch"]

        self.widgets = None
        self.pins = None
        self.kanban = None
        self.wallpapers = None
        self.mixer = None

        self.stack = Stack(
            name="stack",
            transition_type="slide-left-right",
            transition_duration=500,
            v_expand=True,
            v_align="fill",
            h_expand=True,
            h_align="fill",
        )

        self.stack.set_homogeneous(False)

        self.switcher = Gtk.StackSwitcher(
            name="switcher",
            spacing=8,
        )

        if data.SHOW_DASHBOARD_WIDGETS:
            self.widgets = Widgets(notch=self.notch)
            self.stack.add_titled(self.widgets, "widgets", "Widgets")

        if data.SHOW_DASHBOARD_PINS:
            self.pins = Pins()
            self.stack.add_titled(self.pins, "pins", "Pins")

        if data.SHOW_DASHBOARD_KANBAN:
            self.kanban = Kanban()
            self.stack.add_titled(self.kanban, "kanban", "Kanban")

        if data.SHOW_DASHBOARD_WALLPAPERS:
            self.wallpapers = WallpaperSelector()
            self.stack.add_titled(self.wallpapers, "wallpapers", "Wallpapers")

        if data.SHOW_DASHBOARD_MIXER:
            self.mixer = Mixer()
            self.stack.add_titled(self.mixer, "mixer", "Mixer")

        self.switcher.set_stack(self.stack)
        self.switcher.set_hexpand(True)
        self.switcher.set_homogeneous(True)
        self.switcher.set_can_focus(True)

        self.stack.connect("notify::visible-child", self.on_visible_child_changed)

        self.add(self.switcher)
        self.add(self.stack)
        
        if len(self.stack.get_children()) <= 1:
            self.switcher.set_visible(False)

        if data.PANEL_THEME == "Panel" and (
            data.BAR_POSITION in ["Left", "Right"]
            or data.PANEL_POSITION in ["Start", "End"]
        ):
            GLib.idle_add(self._setup_switcher_icons)

        self.show_all()

    def _setup_switcher_icons(self):
        icon_details_map = {}
        if self.widgets:
            icon_details_map["Widgets"] = {"icon": icons.widgets, "name": "widgets"}
        if self.pins:
            icon_details_map["Pins"] = {"icon": icons.pins, "name": "pins"}
        if self.kanban:
            icon_details_map["Kanban"] = {"icon": icons.kanban, "name": "kanban"}
        if self.wallpapers:
            icon_details_map["Wallpapers"] = {"icon": icons.wallpapers, "name": "wallpapers"}
        if self.mixer:
            icon_details_map["Mixer"] = {"icon": icons.speaker, "name": "mixer"}
        
        buttons = self.switcher.get_children()
        for btn in buttons:
            if isinstance(btn, Gtk.ToggleButton):
                original_gtk_label = None
                for child_widget in btn.get_children():
                    if isinstance(child_widget, Gtk.Label):
                        original_gtk_label = child_widget
                        break

                if original_gtk_label:
                    label_text = original_gtk_label.get_text()
                    if label_text in icon_details_map:
                        details = icon_details_map[label_text]
                        icon_markup = details["icon"]
                        css_name_suffix = details["name"]

                        btn.remove(original_gtk_label)

                        new_icon_label = Label(
                            name=f"switcher-icon-{css_name_suffix}", markup=icon_markup
                        )
                        btn.add(new_icon_label)
                        new_icon_label.show_all()
        return GLib.SOURCE_REMOVE

    def go_to_next_child(self):
        children = self.stack.get_children()
        if not children:
            return
        current_index = self.get_current_index(children)
        next_index = (current_index + 1) % len(children)
        self.stack.set_visible_child(children[next_index])

    def go_to_previous_child(self):
        children = self.stack.get_children()
        if not children:
            return
        current_index = self.get_current_index(children)
        previous_index = (current_index - 1 + len(children)) % len(children)
        self.stack.set_visible_child(children[previous_index])

    def get_current_index(self, children):
        current_child = self.stack.get_visible_child()
        return children.index(current_child) if current_child in children else -1

    def on_visible_child_changed(self, stack, param):
        visible = stack.get_visible_child()
        if self.wallpapers and visible == self.wallpapers:
            self.wallpapers.search_entry.set_text("")
            self.wallpapers.search_entry.grab_focus()

    def go_to_section(self, section_name):
        """Navigate to a specific section in the dashboard."""
        if section_name == "widgets" and self.widgets:
            self.stack.set_visible_child(self.widgets)
        elif section_name == "pins" and self.pins:
            self.stack.set_visible_child(self.pins)
        elif section_name == "kanban" and self.kanban:
            self.stack.set_visible_child(self.kanban)
        elif section_name == "wallpapers" and self.wallpapers:
            self.stack.set_visible_child(self.wallpapers)
        elif section_name == "mixer" and self.mixer:
            self.stack.set_visible_child(self.mixer)
