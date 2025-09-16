from typing import Any, List, Literal

import gi
from fabric.core.service import Property, Service, Signal
from fabric.utils import bulk_connect, exec_shell_command_async
from gi.repository import Gio
from loguru import logger

try:
    gi.require_version("NM", "1.0")
    from gi.repository import NM
except (ValueError, ImportError):
    logger.error("Failed to start network manager")
    NM = None


class Wifi(Service):
    """A service to manage the wifi connection."""

    @Signal
    def changed(self) -> None: ...

    @Signal
    def enabled(self) -> bool: ...

    def __init__(self, client: NM.Client, device: NM.DeviceWifi, **kwargs):
        self._client: NM.Client = client
        self._device: NM.DeviceWifi = device
        self._ap: NM.AccessPoint | None = None
        self._ap_signal: int | None = None
        super().__init__(**kwargs)

        self._client.connect(
            "notify::wireless-enabled",
            lambda *args: self.notifier("enabled", args),
        )
        if self._device:
            bulk_connect(
                self._device,
                {
                    "notify::active-access-point": lambda *args: self._activate_ap(),
                    "access-point-added": lambda *args: self.emit("changed"),
                    "access-point-removed": lambda *args: self.emit("changed"),
                    "state-changed": lambda *args: self.ap_update(),
                },
            )
            self._activate_ap()

    def ap_update(self):
        self.emit("changed")
        for sn in [
            "enabled", "internet", "strength", "frequency",
            "access-points", "ssid", "state", "icon-name",
        ]:
            self.notify(sn)

    def _activate_ap(self):
        if self._ap and self._ap_signal is not None:
            self._ap.disconnect(self._ap_signal)
        self._ap = self._device.get_active_access_point()
        if not self._ap:
            return

        self._ap_signal = self._ap.connect(
            "notify::strength", lambda *args: self.ap_update()
        )

    def toggle_wifi(self):
        self._client.wireless_set_enabled(not self._client.wireless_get_enabled())

    def scan(self):
        self._device.request_scan_async(
            None,
            lambda device, result: [
                device.request_scan_finish(result),
                self.emit("changed"),
            ],
        )

    def notifier(self, name: str, *args):
        self.notify(name)
        self.emit("changed")
        return

    @Property(bool, "read-write", default_value=False)
    def enabled(self) -> bool:
        return bool(self._client.wireless_get_enabled())

    @enabled.setter
    def enabled(self, value: bool):
        self._client.wireless_set_enabled(value)

    @Property(int, "readable")
    def strength(self):
        return self._ap.get_strength() if self._ap else -1

    @Property(str, "readable")
    def icon_name(self):
        if not self._ap:
            return "network-wireless-disabled-symbolic"

        if self.internet == "activated":
            return {
                80: "network-wireless-signal-excellent-symbolic",
                60: "network-wireless-signal-good-symbolic",
                40: "network-wireless-signal-ok-symbolic",
                20: "network-wireless-signal-weak-symbolic",
                0: "network-wireless-signal-none-symbolic",
            }.get(
                min(80, 20 * round(self._ap.get_strength() / 20)),
                "network-wireless-no-route-symbolic",
            )
        if self.internet == "activating":
            return "network-wireless-acquiring-symbolic"

        return "network-wireless-offline-symbolic"

    @Property(int, "readable")
    def frequency(self):
        return self._ap.get_frequency() if self._ap else -1

    @Property(str, "readable")
    def internet(self):
        active_conn = self._device.get_active_connection()
        if not active_conn:
            return "deactivated"
        return {
            NM.ActiveConnectionState.ACTIVATED: "activated",
            NM.ActiveConnectionState.ACTIVATING: "activating",
            NM.ActiveConnectionState.DEACTIVATING: "deactivating",
            NM.ActiveConnectionState.DEACTIVATED: "deactivated",
        }.get(
            active_conn.get_state(),
            "unknown",
        )

    @Property(object, "readable")
    def access_points(self) -> List[object]:
        points: list[NM.AccessPoint] = self._device.get_access_points()

        def make_ap_dict(ap: NM.AccessPoint):
            return {
                "bssid": ap.get_bssid(),
                "last_seen": ap.get_last_seen(),
                "ssid": NM.utils_ssid_to_utf8(ap.get_ssid().get_data())
                if ap.get_ssid()
                else "Unknown",
                "active-ap": self._ap,
                "strength": ap.get_strength(),
                "frequency": ap.get_frequency(),
                "icon-name": {
                    80: "network-wireless-signal-excellent-symbolic",
                    60: "network-wireless-signal-good-symbolic",
                    40: "network-wireless-signal-ok-symbolic",
                    20: "network-wireless-signal-weak-symbolic",
                    0: "network-wireless-signal-none-symbolic",
                }.get(
                    min(80, 20 * round(ap.get_strength() / 20)),
                    "network-wireless-no-route-symbolic",
                ),
            }

        return list(map(make_ap_dict, points))

    @Property(str, "readable")
    def ssid(self):
        if not self._ap:
            return "Disconnected"
        ssid_obj = self._ap.get_ssid()
        if not ssid_obj:
            return "Unknown"
        ssid = ssid_obj.get_data()
        return NM.utils_ssid_to_utf8(ssid) if ssid else "Unknown"

    @Property(str, "readable")
    def state(self):
        return {
            NM.DeviceState.UNMANAGED: "unmanaged",
            NM.DeviceState.UNAVAILABLE: "unavailable",
            NM.DeviceState.DISCONNECTED: "disconnected",
            NM.DeviceState.PREPARE: "prepare",
            NM.DeviceState.CONFIG: "config",
            NM.DeviceState.NEED_AUTH: "need_auth",
            NM.DeviceState.IP_CONFIG: "ip_config",
            NM.DeviceState.IP_CHECK: "ip_check",
            NM.DeviceState.SECONDARIES: "secondaries",
            NM.DeviceState.ACTIVATED: "activated",
            NM.DeviceState.DEACTIVATING: "deactivating",
            NM.DeviceState.FAILED: "failed",
        }.get(self._device.get_state(), "unknown")


class Ethernet(Service):
    """A service to manage the ethernet connection."""

    @Signal
    def changed(self) -> None: ...

    @Signal
    def enabled(self) -> bool: ...

    @Property(int, "readable")
    def speed(self) -> int:
        return self._device.get_speed()

    @Property(str, "readable")
    def internet(self) -> str:
        active_conn = self._device.get_active_connection()
        if not active_conn:
            return "disconnected"
        return {
            NM.ActiveConnectionState.ACTIVATED: "activated",
            NM.ActiveConnectionState.ACTIVATING: "activating",
            NM.ActiveConnectionState.DEACTIVATING: "deactivating",
            NM.ActiveConnectionState.DEACTIVATED: "deactivated",
        }.get(
            active_conn.get_state(),
            "disconnected",
        )

    @Property(str, "readable")
    def icon_name(self) -> str:
        network = self.internet
        if network == "activated":
            return "network-wired-symbolic"

        elif network == "activating":
            return "network-wired-acquiring-symbolic"

        elif self._device.get_connectivity(None) != NM.ConnectivityState.FULL:
            return "network-wired-no-route-symbolic"

        return "network-wired-disconnected-symbolic"

    def __init__(self, client: NM.Client, device: NM.DeviceEthernet, **kwargs) -> None:
        super().__init__(**kwargs)
        self._client: NM.Client = client
        self._device: NM.DeviceEthernet = device

        for pn in (
            "active-connection",
            "icon-name",
            "internet",
            "speed",
            "state",
        ):
            self._device.connect(f"notify::{pn}", lambda *_: self.notifier(pn))

        self._device.connect("notify::speed", lambda *_: print(_))

    def notifier(self, pn):
        self.notify(pn)
        self.emit("changed")


class NetworkClient(Service):
    """A service to manage the network connections."""

    @Signal
    def device_ready(self) -> None: ...

    def __init__(self, **kwargs):
        self._client: NM.Client | None = None
        self.wifi_device: Wifi | None = None
        self.ethernet_device: Ethernet | None = None
        super().__init__(**kwargs)
        if NM:
            NM.Client.new_async(
                cancellable=None,
                callback=self._init_network_client,
            )

    def _init_network_client(self, source_object, task: Gio.Task):
        try:
            self._client = NM.Client.new_finish(task)
            if not self._client:
                logger.error("NetworkClient failed to initialize: NM.Client.new_finish() returned None.")
                return

            self._client.connect("notify::primary-connection", self._on_primary_connection_changed)
            self._client.connect("notify::devices", self._on_primary_connection_changed)

            wifi_device: NM.DeviceWifi | None = self._get_device(NM.DeviceType.WIFI)
            ethernet_device: NM.DeviceEthernet | None = self._get_device(NM.DeviceType.ETHERNET)

            if wifi_device:
                self.wifi_device = Wifi(self._client, wifi_device)
            if ethernet_device:
                self.ethernet_device = Ethernet(client=self._client, device=ethernet_device)
            
            if wifi_device or ethernet_device:
                self.emit("device-ready")

            self.notify("primary-device")
            self.notify("primary_connection")
        except Exception as e:
            logger.error(f"NetworkClient failed during async initialization: {e}", exc_info=True)

    def _get_device(self, device_type) -> Any:
        if not self._client:
            return None
        devices: List[NM.Device] = self._client.get_devices()
        return next(
            (
                x
                for x in devices
                if x.get_device_type() == device_type
            ),
            None,
        )

    def _get_primary_device(self) -> Literal["wifi", "wired"] | None:
        if not self._client:
            return None
        connection = self._client.get_primary_connection()
        if connection is None:
            return None
        conn_type = connection.get_connection_type()
        if "wireless" in conn_type:
            return "wifi"
        if "ethernet" in conn_type:
            return "wired"
        return None
    
    def _on_primary_connection_changed(self, *args):
        self.notify("primary-device")
        self.notify("primary_connection")

    def connect_wifi_bssid(self, bssid):
        exec_shell_command_async(
            f"nmcli device wifi connect {bssid}", lambda *args: print(args)
        )

    @Property(str, "readable")
    def primary_device(self) -> Literal["wifi", "wired"] | None:
        return self._get_primary_device()

    @Property(object, "readable")
    def primary_connection(self) -> NM.Connection | None:
        if not self._client:
            return None
        return self._client.get_primary_connection()
