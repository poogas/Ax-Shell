import os

import gi

gi.require_version("GLib", "2.0")
import setproctitle
from fabric import Application
from fabric.utils import exec_shell_command_async, get_relative_path
from gi.repository import GLib

from config.data import APP_NAME, APP_NAME_CAP, CACHE_DIR, CONFIG_FILE, HOME_DIR
from modules.bar import Bar
from modules.corners import Corners
from modules.dock import Dock
from modules.notch import Notch
from modules.notifications import NotificationPopup
from modules.updater import run_updater

fonts_updated_file = f"{CACHE_DIR}/fonts_updated"

if __name__ == "__main__":
    setproctitle.setproctitle(APP_NAME)

    if not os.path.isfile(CONFIG_FILE):
        config_script_path = get_relative_path("config/config.py")
        exec_shell_command_async(f"python {config_script_path}")

current_wallpaper_link = os.path.expanduser("~/.current.wall")

# Пытаемся получить актуальный путь из переменной окружения Nix
nix_wallpapers_path = os.getenv("AX_SHELL_WALLPAPERS_DIR_DEFAULT")
target_wallpaper_file = None

if nix_wallpapers_path:
    target_wallpaper_file = os.path.join(nix_wallpapers_path, "example-1.jpg")
else:
    # Запасной вариант для non-Nix систем
    target_wallpaper_file = os.path.expanduser(
        f"~/.config/{APP_NAME_CAP}/assets/wallpapers_example/example-1.jpg"
    )

# --- Основная логика проверки и обновления ссылки ---
needs_update = True
if os.path.islink(current_wallpaper_link):
    # Если ссылка существует, проверяем, куда она указывает
    current_target = os.readlink(current_wallpaper_link)
    if current_target == target_wallpaper_file:
        # Ссылка уже актуальна, ничего делать не нужно
        needs_update = False

if needs_update and target_wallpaper_file and os.path.exists(os.path.dirname(target_wallpaper_file)):
    # Если ссылка неактуальна или отсутствует, обновляем её
    if os.path.lexists(current_wallpaper_link):
        # os.lexists находит и файл, и битую ссылку, в отличие от os.path.exists
        os.remove(current_wallpaper_link)
    
    # Создаем новую, правильную ссылку
    os.symlink(target_wallpaper_file, current_wallpaper_link)
    print(f"Updated symlink: {current_wallpaper_link} -> {target_wallpaper_file}")

    # Load configuration
    from config.data import load_config

    config = load_config()

    GLib.idle_add(run_updater)
    # Every hour
    GLib.timeout_add(3600000, run_updater)

    corners = Corners()
    bar = Bar()
    notch = Notch()
    dock = Dock()
    bar.notch = notch
    notch.bar = bar
    notification = NotificationPopup(widgets=notch.dashboard.widgets)

    # Set corners visibility based on config
    corners_visible = config.get("corners_visible", True)
    corners.set_visible(corners_visible)

    app = Application(
        f"{APP_NAME}", bar, notch, dock, notification, corners
    )  # Make sure corners is added to the app

    def set_css():
        app.set_stylesheet_from_file(
            get_relative_path("main.css"),
        )

    app.set_css = set_css

    app.set_css()

    app.run()
