import urllib.parse

import gi
import requests
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from gi.repository import GLib
from loguru import logger

gi.require_version("Gtk", "3.0")
import config.data as data
import modules.icons as icons


class Weather(Button):
    def __init__(self, **kwargs) -> None:
        super().__init__(name="weather", orientation="h", spacing=8, **kwargs)
        self.label = Label(name="weather-label", markup=icons.loader)
        self.add(self.label)
        self.show_all()
        self.enabled = True
        self.has_weather_data = False
        self.session = requests.Session()
        
        # Schedule the initial fetch and the start of the recurring timer.
        GLib.timeout_add_seconds(3, self._initial_fetch_and_start_updates)

    def set_visible(self, visible):
        """Override to track external visibility setting"""
        self.enabled = visible
        # Only show the widget if it's enabled AND we have valid weather data.
        super().set_visible(self.enabled and self.has_weather_data)

    def _initial_fetch_and_start_updates(self):
        # This function runs only ONCE, 3 seconds after startup.
        self.fetch_weather() # Perform the first fetch.
        # After the first fetch, start the main timer that repeats every 10 minutes.
        GLib.timeout_add_seconds(600, self.fetch_weather)
        # Return False to make this initial timer stop and not repeat.
        return False

    def fetch_weather(self):
        # This function is now used for all fetches (initial and recurring).
        GLib.Thread.new("weather-fetch", self._fetch_weather_thread, None)
        # Return True so that when called by the 600s timer, it keeps repeating.
        return True

    def _fetch_weather_thread(self, user_data):
        url = "https://wttr.in/?format=%c+%t" if not data.VERTICAL else "https://wttr.in/?format=%c"
        tooltip_url = "https://wttr.in/?format=%l:+%C,+%t+(%f),+Humidity:+%h,+Wind:+%w"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            weather_data = response.text.strip()
            if "Unknown" in weather_data or "Sorry" in weather_data:
                self.has_weather_data = False
                GLib.idle_add(self.set_visible, False)
            else:
                self.has_weather_data = True
                tooltip_response = self.session.get(tooltip_url, timeout=10)
                if tooltip_response.ok:
                    tooltip_text = tooltip_response.text.strip()
                    GLib.idle_add(self.set_tooltip_text, tooltip_text)
                
                GLib.idle_add(self.label.set_label, weather_data.replace(" ", ""))
                GLib.idle_add(self.set_visible, True)

        except requests.exceptions.RequestException as e:
            # On network error, just schedule a retry in 30 seconds.
            logger.warning(f"Failed to fetch weather ({e}), retrying in 30 seconds.")
            GLib.timeout_add_seconds(30, self.fetch_weather)
