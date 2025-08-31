import os
import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib, Gio
import setproctitle

from fabric import Application
from fabric.utils import get_relative_path
from config.data import APP_NAME, CONFIG_FILE, CURRENT_WALLPAPER_PATH, load_config
from modules.bar import Bar
from modules.corners import Corners
from modules.dock import Dock
from modules.notch import Notch
from modules.notifications import NotificationPopup
from modules.updater import run_updater

class AxShellApp(Application):
    def __init__(self):
        super().__init__(
            APP_NAME,
            application_id=f"com.github.poogas.{APP_NAME}",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        setproctitle.setproctitle(APP_NAME)

        self.ensure_config_file_exists()
        self.ensure_current_wallpaper_exists()
        self.config = load_config()

        self.corners = Corners()
        self.bar = Bar()
        self.notch = Notch()
        self.dock = Dock()
        self.bar.notch = self.notch
        self.notch.bar = self.bar
        self.notification = NotificationPopup(widgets=self.notch.dashboard.widgets)

        self.add_window(self.bar)
        self.add_window(self.notch)
        self.add_window(self.dock)
        self.add_window(self.notification)
        self.add_window(self.corners)

    def do_activate(self):
        super().do_activate()
        corners_visible = self.config.get("corners_visible", True)
        self.corners.set_visible(corners_visible)
        self.set_css()
        GLib.idle_add(run_updater)
        GLib.timeout_add(3600000, run_updater)

    def run_command(self, command: str):
        print(f"Received command: {command}")
        match command:
            case "open_dashboard": self.notch.open_notch("dashboard")
            case "open_launcher": self.notch.open_notch("launcher")
            case "open_bluetooth": self.notch.open_notch("bluetooth")
            case "open_pins": self.notch.open_notch("pins")
            case "open_kanban": self.notch.open_notch("kanban")
            case "open_tmux": self.notch.open_notch("tmux")
            case "open_cliphist": self.notch.open_notch("cliphist")
            case "open_tools": self.notch.open_notch("tools")
            case "open_overview": self.notch.open_notch("overview")
            case "open_wallpapers": self.notch.open_notch("wallpapers")
            case "open_mixer": self.notch.open_notch("mixer")
            case "open_emoji": self.notch.open_notch("emoji")
            case "open_power": self.notch.open_notch("power")
            case "reload_css": self.set_css()
            case "random_wallpaper": self.notch.dashboard.wallpapers.set_random_wallpaper(None, external=True)
            case "toggle_caffeine": self.notch.dashboard.widgets.buttons.caffeine_button.toggle_inhibit(external=True)
            case _:
                print(f"Unknown command: {command}")

    def set_css(self):
        self.set_stylesheet_from_file(get_relative_path("main.css"))

    def ensure_config_file_exists(self):
        if not os.path.isfile(CONFIG_FILE):
            print(f"WARNING: Config file not found at {CONFIG_FILE}")

    def ensure_current_wallpaper_exists(self):
        if not os.path.exists(CURRENT_WALLPAPER_PATH):
            os.makedirs(os.path.dirname(CURRENT_WALLPAPER_PATH), exist_ok=True)
            nix_wallpapers_path = os.getenv("AX_SHELL_WALLPAPERS_DIR_DEFAULT")
            if nix_wallpapers_path:
                source_wallpaper = os.path.join(nix_wallpapers_path, "example-1.jpg")
                if os.path.exists(source_wallpaper):
                    os.symlink(source_wallpaper, CURRENT_WALLPAPER_PATH)
            else:
                print("WARNING: AX_SHELL_WALLPAPERS_DIR_DEFAULT not set.")

if __name__ == "__main__":
    app = AxShellApp()
    app.run()
