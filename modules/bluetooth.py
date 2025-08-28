from fabric.bluetooth import BluetoothClient, BluetoothDevice
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.image import Image
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow
from loguru import logger
import subprocess
from gi.repository import GLib

import modules.icons as icons

def send_notification(summary, body, icon):
    """
    Asynchronously sends a system notification using the notify-send utility,
    without blocking the main thread.
    """
    command = ["notify-send", "-a", "Bluetooth", "-i", icon, summary, body]
    try:
        # Popen does not wait for the command to complete.
        subprocess.Popen(command)
        logger.info(f"Sent notification command: {summary} - {body}")
    except FileNotFoundError:
        logger.error("Command 'notify-send' not found. Please install libnotify.")
    except Exception as e:
        logger.exception(f"Failed to send notification: {e}")

class BluetoothDeviceSlot(CenterBox):
    def __init__(self, device: BluetoothDevice, **kwargs):
        super().__init__(name="bluetooth-device", **kwargs)
        self.device = device
        self.previous_connected_state = device.connected # Store the initial state
        
        self.device.connect("changed", self.on_changed)
        self.device.connect(
            "notify::closed", lambda *_: self.device.closed and self.destroy()
        )

        self.connection_label = Label(name="bluetooth-connection", markup=icons.bluetooth_disconnected)
        self.connect_button = Button(
            name="bluetooth-connect",
            label="Connect",
            on_clicked=lambda *_: self.device.set_connecting(not self.device.connected),
        )

        self.start_children = [
            Box(
                spacing=8,
                h_expand=True,
                h_align="fill",
                children=[
                    Image(icon_name=device.icon_name + "-symbolic", size=16),
                    Label(label=device.name, h_expand=True, h_align="start", ellipsization="end"),
                    self.connection_label,
                ],
            )
        ]
        self.end_children = [self.connect_button]

        self.on_changed(self.device) # Call to set the initial UI state

    def on_changed(self, device, *_):
        # Notification logic
        if device.connected != self.previous_connected_state:
            logger.info(f"Device '{device.name}' connection state changed from {self.previous_connected_state} to {device.connected}")
            if device.connected:
                summary = f"{device.name}"
                body = "Device connected"
                icon = "bluetooth-active-symbolic"
            else:
                summary = f"{device.name}"
                body = "Device disconnected"
                icon = "bluetooth-disabled-symbolic"
            
            # Send notification
            GLib.idle_add(send_notification, summary, body, icon)
        
        self.previous_connected_state = device.connected

        # UI update logic
        self.connection_label.set_markup(
            icons.bluetooth_connected if device.connected else icons.bluetooth_disconnected
        )
        if device.connecting:
            self.connect_button.set_label("Connecting...")
            self.connect_button.set_sensitive(False)
        else:
            self.connect_button.set_label("Disconnect" if device.connected else "Connect")
            self.connect_button.set_sensitive(True)

        if device.connected:
            self.connect_button.add_style_class("connected")
        else:
            self.connect_button.remove_style_class("connected")

class BluetoothConnections(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="bluetooth",
            spacing=4,
            orientation="vertical",
            **kwargs,
        )

        self.widgets = kwargs["widgets"]

        self.buttons = self.widgets.buttons.bluetooth_button
        self.bt_status_text = self.buttons.bluetooth_status_text
        self.bt_status_button = self.buttons.bluetooth_status_button
        self.bt_icon = self.buttons.bluetooth_icon
        self.bt_label = self.buttons.bluetooth_label
        self.bt_menu_button = self.buttons.bluetooth_menu_button
        self.bt_menu_label = self.buttons.bluetooth_menu_label

        self.client = BluetoothClient(on_device_added=self.on_device_added)
        self.scan_label = Label(name="bluetooth-scan-label", markup=icons.radar)
        self.scan_button = Button(
            name="bluetooth-scan",
            child=self.scan_label,
            tooltip_text="Scan for Bluetooth devices",
            on_clicked=lambda *_: self.client.toggle_scan()
        )
        self.back_button = Button(
            name="bluetooth-back",
            child=Label(name="bluetooth-back-label", markup=icons.chevron_left),
            on_clicked=lambda *_: self.widgets.show_notif()
        )

        self.client.connect("notify::enabled", self.status_label)
        self.client.connect("notify::scanning", self.update_scan_label)

        self.paired_box = Box(spacing=2, orientation="vertical")
        self.available_box = Box(spacing=2, orientation="vertical")

        content_box = Box(spacing=4, orientation="vertical")
        content_box.add(self.paired_box)
        content_box.add(Label(name="bluetooth-section", label="Available"))
        content_box.add(self.available_box)

        self.children = [
            CenterBox(
                name="bluetooth-header",
                start_children=[self.back_button],
                center_children=[Label(name="bluetooth-text", label="Bluetooth Devices")],
                end_children=[self.scan_button]
            ),
            ScrolledWindow(
                name="bluetooth-devices",
                min_content_size=(-1, -1),
                child=content_box,
                v_expand=True,
                propagate_width=False,
                propagate_height=False,
            ),
        ]

        # Use GLib.idle_add to ensure client properties are ready before we check them
        GLib.idle_add(self.client.notify, "scanning")
        GLib.idle_add(self.client.notify, "enabled")

    def status_label(self, *args):
        if self.client.enabled:
            self.bt_status_text.set_label("Enabled")
            for i in [self.bt_status_button, self.bt_status_text, self.bt_icon, self.bt_label, self.bt_menu_button, self.bt_menu_label]:
                i.remove_style_class("disabled")
            self.bt_icon.set_markup(icons.bluetooth)
        else:
            self.bt_status_text.set_label("Disabled")
            for i in [self.bt_status_button, self.bt_status_text, self.bt_icon, self.bt_label, self.bt_menu_button, self.bt_menu_label]:
                i.add_style_class("disabled")
            self.bt_icon.set_markup(icons.bluetooth_off)

    def on_device_added(self, client: BluetoothClient, address: str):
        if not (device := client.get_device(address)):
            return
        slot = BluetoothDeviceSlot(device)

        if device.paired:
            self.paired_box.add(slot)
        else:
            self.available_box.add(slot)

    def update_scan_label(self, *args):
        if self.client.scanning:
            self.scan_label.add_style_class("scanning")
            self.scan_button.add_style_class("scanning")
            self.scan_button.set_tooltip_text("Stop scanning for Bluetooth devices")
        else:
            self.scan_label.remove_style_class("scanning")
            self.scan_button.remove_style_class("scanning")
            self.scan_button.set_tooltip_text("Scan for Bluetooth devices")
