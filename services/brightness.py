import os

from fabric.core.service import Property, Service, Signal
from fabric.utils import exec_shell_command_async, monitor_file
from gi.repository import GLib
from loguru import logger

import utils.functions as helpers
from utils.colors import Colors


def exec_brightnessctl_async(args: str):
    """
    Asynchronously executes the brightnessctl command.

    Checks for the existence of the 'brightnessctl' executable and logs an error
    if it's not found.
    """
    if not helpers.executable_exists("brightnessctl"):
        logger.error(f"{Colors.ERROR}Command brightnessctl not found")
        return
    exec_shell_command_async(f"brightnessctl {args}", lambda _: None)


class Brightness(Service):
    """
    Service to manage screen brightness levels.

    This class handles discovery of backlight devices and provides methods
    to read and write brightness values. It uses a singleton pattern to ensure
    only one instance manages the device.
    """

    instance = None

    @staticmethod
    def get_initial():
        """Gets the singleton instance of the Brightness service."""
        if Brightness.instance is None:
            Brightness.instance = Brightness()
        return Brightness.instance

    @Signal
    def screen(self, value: int) -> None:
        """Signal emitted when the screen brightness changes."""
        pass

    @Signal
    def ready(self) -> None:
        """Signal emitted when the brightness device is found and initialized."""
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_device = None
        self.screen_backlight_path = ""
        self.max_screen = -1
        self.screen_monitor = None
        self.init_retries = 0
        self.max_init_retries = 35

        self._is_writing = False
        self._pending_write_value = None

        logger.info("[Brightness] Service created. Starting device discovery...")
        GLib.timeout_add_seconds(1, self.poll_for_device)

    def poll_for_device(self) -> bool:
        """Polls the system for a backlight device."""
        try:
            devices = os.listdir("/sys/class/backlight")
            if devices:
                self.screen_device = devices[0]
                self.screen_backlight_path = (
                    f"/sys/class/backlight/{self.screen_device}"
                )
                brightness_file = os.path.join(
                    self.screen_backlight_path, "brightness"
                )

                if os.path.exists(brightness_file):
                    logger.info(
                        f"{Colors.INFO}Backlight device '{self.screen_device}' found and ready."
                    )
                    self.finalize_initialization()
                    return GLib.SOURCE_REMOVE
                elif self.init_retries == 0:
                    logger.info(
                        f"Backlight device '{self.screen_device}' found, waiting for brightness file..."
                    )
        except FileNotFoundError:
            if self.init_retries == 0:
                logger.info("Waiting for /sys/class/backlight to appear...")

        self.init_retries += 1
        if self.init_retries > self.max_init_retries:
            logger.error(
                f"{Colors.ERROR}Failed to find backlight device after {self.max_init_retries} seconds."
            )
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    def finalize_initialization(self) -> None:
        """Finalizes the service initialization once a device is found."""
        self.max_screen = self.do_read_max_brightness(self.screen_backlight_path)
        if self.max_screen <= 0:
            logger.error(
                f"{Colors.ERROR}Could not read max_brightness for {self.screen_device}."
            )
            return

        brightness_path = os.path.join(self.screen_backlight_path, "brightness")
        self.screen_monitor = monitor_file(brightness_path)
        self.screen_monitor.connect(
            "changed",
            lambda _, file, *args: self.emit(
                "screen", round(int(file.load_bytes()[0].get_data()))
            ),
        )
        logger.info(
            f"{Colors.INFO}Brightness service initialized for device: {self.screen_device}"
        )
        self.notify("screen-brightness")
        self.emit("ready")

    def do_read_max_brightness(self, path: str) -> int:
        """Reads the maximum brightness value from the sysfs path."""
        max_brightness_path = os.path.join(path, "max_brightness")
        try:
            with open(max_brightness_path) as f:
                return int(f.readline())
        except (IOError, ValueError, FileNotFoundError) as e:
            logger.error(f"Error reading max brightness from {max_brightness_path}: {e}")
            return -1

    @Property(int, "read-write")
    def screen_brightness(self) -> int:
        """The current screen brightness value."""
        if not self.screen_device:
            return -1
        brightness_path = os.path.join(self.screen_backlight_path, "brightness")
        try:
            with open(brightness_path) as f:
                return int(f.readline())
        except (IOError, ValueError, FileNotFoundError):
            return -1

    @screen_brightness.setter
    def screen_brightness(self, value: int) -> None:
        """Sets the screen brightness value."""
        if not self.screen_device or self.max_screen <= 0:
            return
        self._pending_write_value = int(max(0, min(value, self.max_screen)))
        self._process_write_queue()

    def _process_write_queue(self) -> None:
        """
        Processes pending brightness write operations to avoid race conditions.
        """
        if self._is_writing or self._pending_write_value is None:
            return

        self._is_writing = True
        value_to_write = self._pending_write_value
        self._pending_write_value = None

        command = f"brightnessctl --device '{self.screen_device}' set {value_to_write}"
        exec_shell_command_async(command, self._on_write_complete)

    def _on_write_complete(self, success: bool) -> None:
        """Callback executed after a write operation completes."""
        self._is_writing = False
        self._process_write_queue()
