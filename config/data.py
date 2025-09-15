import json
import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib

from .settings_constants import DEFAULTS, APP_NAME, APP_NAME_CAP

HOME_DIR = os.path.expanduser("~")
CACHE_DIR = os.path.join(GLib.get_user_cache_dir(), APP_NAME)
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME_DIR, ".config"))
XDG_STATE_HOME = os.environ.get("XDG_STATE_HOME", os.path.join(HOME_DIR, ".local/state"))
STATE_DIR = os.path.join(XDG_STATE_HOME, APP_NAME)
os.makedirs(STATE_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(XDG_CONFIG_HOME, APP_NAME, "config.json")
CURRENT_WALLPAPER_PATH = os.path.join(XDG_CONFIG_HOME, APP_NAME, "current.wall")
MATUGEN_STATE_FILE = os.path.join(STATE_DIR, "matugen")

USERNAME = os.getlogin()
HOSTNAME = os.uname().nodename
screen = Gdk.Screen.get_default()
CURRENT_WIDTH = screen.get_width()
CURRENT_HEIGHT = screen.get_height()

def load_config_file():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[ERROR] Failed to load or read {CONFIG_FILE}: {e}")
        return {}

config = load_config_file()

WALLPAPERS_DIR = config.get("wallpapers_dir", DEFAULTS["wallpapers_dir"])
BAR_POSITION = config.get("bar_position", DEFAULTS["bar_position"])
VERTICAL = BAR_POSITION in ["Left", "Right"]
CENTERED_BAR = config.get("centered_bar", DEFAULTS["centered_bar"])
DATETIME_12H_FORMAT = config.get("datetime_12h_format", DEFAULTS["datetime_12h_format"])
TERMINAL_COMMAND = config.get("terminal_command", DEFAULTS["terminal_command"])
DOCK_ENABLED = config.get("dock_enabled", DEFAULTS["dock_enabled"])
DOCK_ALWAYS_OCCLUDED = config.get("dock_always_occluded", DEFAULTS["dock_always_occluded"])
DOCK_ICON_SIZE = config.get("dock_icon_size", DEFAULTS["dock_icon_size"])
BAR_WORKSPACE_SHOW_NUMBER = config.get("bar_workspace_show_number", DEFAULTS["bar_workspace_show_number"])
BAR_WORKSPACE_USE_CHINESE_NUMERALS = config.get("bar_workspace_use_chinese_numerals", DEFAULTS["bar_workspace_use_chinese_numerals"])
BAR_HIDE_SPECIAL_WORKSPACE = config.get("bar_hide_special_workspace", DEFAULTS["bar_hide_special_workspace"])
BAR_THEME = config.get("bar_theme", DEFAULTS["bar_theme"])
DOCK_THEME = config.get("dock_theme", DEFAULTS["dock_theme"])
PANEL_THEME = config.get("panel_theme", DEFAULTS["panel_theme"])
PANEL_POSITION = config.get("panel_position", DEFAULTS["panel_position"])
NOTIF_POS = config.get("notif_pos", DEFAULTS["notif_pos"])

BAR_METRICS_DISKS = config.get("bar_metrics_disks", DEFAULTS["bar_metrics_disks"])
METRICS_VISIBLE = config.get("metrics_visible", DEFAULTS["metrics_visible"])
METRICS_SMALL_VISIBLE = config.get("metrics_small_visible", DEFAULTS["metrics_small_visible"])

BAR_COMPONENTS_VISIBILITY = {
    key: config.get(f"bar_{key}_visible", DEFAULTS.get(f"bar_{key}_visible", True))
    for key in [
        "button_apps", "systray", "control", "network", "button_tools",
        "sysprofiles", "button_overview", "ws_container", "weather",
        "battery", "metrics", "language", "date_time", "button_power"
    ]
}
