import config.data as data
import modules.icons as icons
from fabric.audio.service import Audio
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.widgets.eventbox import EventBox
from fabric.widgets.label import Label
from fabric.widgets.overlay import Overlay
from fabric.widgets.scale import Scale
from gi.repository import Gdk, GLib
from services.brightness import Brightness


class VolumeSlider(Scale):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-slider",
            orientation="h",
            h_expand=True,
            h_align="fill",
            has_origin=True,
            increments=(0.01, 0.1),
            **kwargs,
        )
        self.audio = Audio()
        self._is_programmatic_change = False

        self.audio.connect("notify::speaker", self.on_new_speaker)
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)

        self.connect("value-changed", self.on_value_changed)
        self.add_style_class("vol")
        self.on_speaker_changed()

    def on_new_speaker(self, *args):
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
            self.on_speaker_changed()

    def on_value_changed(self, _):
        if self._is_programmatic_change:
            return
        if self.audio.speaker:
            self.audio.speaker.volume = self.get_value() * 100

    def on_speaker_changed(self, *_):
        if not self.audio.speaker:
            return

        new_value = self.audio.speaker.volume / 100
        if abs(self.get_value() - new_value) > 0.001:
            self._is_programmatic_change = True
            self.set_value(new_value)
            self._is_programmatic_change = False

        if self.audio.speaker.muted:
            self.add_style_class("muted")
        else:
            self.remove_style_class("muted")


class MicSlider(Scale):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-slider",
            orientation="h",
            h_expand=True,
            has_origin=True,
            increments=(0.01, 0.1),
            **kwargs,
        )
        self.audio = Audio()
        self._is_programmatic_change = False

        self.audio.connect("notify::microphone", self.on_new_microphone)
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)

        self.connect("value-changed", self.on_value_changed)
        self.add_style_class("mic")
        self.on_microphone_changed()

    def on_new_microphone(self, *args):
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
            self.on_microphone_changed()

    def on_value_changed(self, _):
        if self._is_programmatic_change:
            return
        if self.audio.microphone:
            self.audio.microphone.volume = self.get_value() * 100

    def on_microphone_changed(self, *_):
        if not self.audio.microphone:
            return

        new_value = self.audio.microphone.volume / 100
        if abs(self.get_value() - new_value) > 0.001:
            self._is_programmatic_change = True
            self.set_value(new_value)
            self._is_programmatic_change = False

        if self.audio.microphone.muted:
            self.add_style_class("muted")
        else:
            self.remove_style_class("muted")


class BrightnessSlider(Scale):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-slider",
            orientation="h",
            h_expand=True,
            has_origin=True,
            digits=0,
            **kwargs,
        )
        self.client = Brightness.get_initial()
        self._is_programmatic_change = False

        self.set_range(0, self.client.max_screen)

        adjustment = self.get_adjustment()
        adjustment.set_step_increment(1)
        adjustment.set_page_increment(10)

        self.set_value(self.client.screen_brightness)
        self.add_style_class("brightness")

        self.connect("value-changed", self.on_value_changed)
        self.client.connect("screen", self.on_brightness_changed)
        self.on_brightness_changed(None, None)

    def on_value_changed(self, _):
        if self._is_programmatic_change:
            return

        self.client.screen_brightness = self.get_value()

    def on_brightness_changed(self, client, _):
        new_value = self.client.screen_brightness

        if int(self.get_value()) != new_value:
            self._is_programmatic_change = True
            self.set_value(new_value)
            self._is_programmatic_change = False

        if self.client.max_screen > 0:
            percentage = int((new_value / self.client.max_screen) * 100)
            self.set_tooltip_text(f"{percentage}%")

    def destroy(self):
        super().destroy()


class BrightnessSmall(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar-brightness", **kwargs)
        self.brightness = Brightness.get_initial()

        self.progress_bar = CircularProgressBar(
            name="button-brightness",
            size=28,
            line_width=2,
            start_angle=150,
            end_angle=390,
        )
        self.brightness_label = Label(
            name="brightness-label", markup=icons.brightness_high
        )
        self.brightness_button = Button(child=self.brightness_label)
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=Overlay(child=self.progress_bar, overlays=self.brightness_button),
        )
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)

        self._is_user_scrolling = False
        self._update_source_id = None

        self.brightness.connect("screen", self.on_brightness_changed)
        self.on_brightness_changed()

    def on_scroll(self, widget, event):
        if self.brightness.max_screen <= 0:
            return

        step_size = 5
        current_norm = self.progress_bar.value
        if event.delta_y < 0:
            new_norm = min(current_norm + (step_size / self.brightness.max_screen), 1)
        elif event.delta_y > 0:
            new_norm = max(current_norm - (step_size / self.brightness.max_screen), 0)
        else:
            return

        self._is_user_scrolling = True

        self.progress_bar.value = new_norm

        if self._update_source_id is not None:
            GLib.source_remove(self._update_source_id)

        self._update_source_id = GLib.timeout_add(100, self._update_brightness_callback)

    def _update_brightness_callback(self):
        new_brightness = int(self.progress_bar.value * self.brightness.max_screen)

        if new_brightness != self.brightness.screen_brightness:
            self.brightness.screen_brightness = new_brightness

        self._update_source_id = None
        self._is_user_scrolling = False

        return False

    def on_brightness_changed(self, *args):
        if self._is_user_scrolling:
            return

        if self.brightness.max_screen <= 0:
            return

        normalized = self.brightness.screen_brightness / self.brightness.max_screen

        if abs(self.progress_bar.value - normalized) > 0.001:
            self.progress_bar.value = normalized

        brightness_percentage = int(normalized * 100)
        if brightness_percentage >= 75:
            self.brightness_label.set_markup(icons.brightness_high)
        elif brightness_percentage >= 24:
            self.brightness_label.set_markup(icons.brightness_medium)
        else:
            self.brightness_label.set_markup(icons.brightness_low)
        self.set_tooltip_text(f"{brightness_percentage}%")

    def destroy(self):
        if self._update_source_id is not None:
            GLib.source_remove(self._update_source_id)
        super().destroy()


class VolumeSmall(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar-vol", **kwargs)
        self.audio = Audio()
        self.progress_bar = CircularProgressBar(
            name="button-volume",
            size=28,
            line_width=2,
            start_angle=150,
            end_angle=390,
        )
        self.vol_label = Label(name="vol-label", markup=icons.vol_high)
        self.vol_button = Button(on_clicked=self.toggle_mute, child=self.vol_label)
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=Overlay(child=self.progress_bar, overlays=self.vol_button),
        )
        self.audio.connect("notify::speaker", self.on_new_speaker)
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)
        self.on_speaker_changed()
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)

    def on_new_speaker(self, *args):
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
            self.on_speaker_changed()

    def toggle_mute(self, event):
        current_stream = self.audio.speaker
        if current_stream:
            current_stream.muted = not current_stream.muted
            if current_stream.muted:
                self.on_speaker_changed()
                self.progress_bar.add_style_class("muted")
                self.vol_label.add_style_class("muted")
            else:
                self.on_speaker_changed()
                self.progress_bar.remove_style_class("muted")
                self.vol_label.remove_style_class("muted")

    def on_scroll(self, _, event):
        if not self.audio.speaker:
            return
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if abs(event.delta_y) > 0:
                self.audio.speaker.volume -= event.delta_y
            if abs(event.delta_x) > 0:
                self.audio.speaker.volume += event.delta_x

    def on_speaker_changed(self, *_):
        if not self.audio.speaker:
            return

        vol_high_icon = icons.vol_high
        vol_medium_icon = icons.vol_medium
        vol_mute_icon = icons.vol_off
        vol_off_icon = icons.vol_mute

        if "bluetooth" in self.audio.speaker.icon_name:
            vol_high_icon = icons.bluetooth_connected
            vol_medium_icon = icons.bluetooth
            vol_mute_icon = icons.bluetooth_off
            vol_off_icon = icons.bluetooth_disconnected

        self.progress_bar.value = self.audio.speaker.volume / 100

        if self.audio.speaker.muted:
            self.vol_button.get_child().set_markup(vol_mute_icon)
            self.progress_bar.add_style_class("muted")
            self.vol_label.add_style_class("muted")
            self.set_tooltip_text("Muted")
            return
        else:
            self.progress_bar.remove_style_class("muted")
            self.vol_label.remove_style_class("muted")
        self.set_tooltip_text(f"{round(self.audio.speaker.volume)}%")
        if self.audio.speaker.volume > 74:
            self.vol_button.get_child().set_markup(vol_high_icon)
        elif self.audio.speaker.volume > 0:
            self.vol_button.get_child().set_markup(vol_medium_icon)
        else:
            self.vol_button.get_child().set_markup(vol_off_icon)


class MicSmall(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar-mic", **kwargs)
        self.audio = Audio()
        self.progress_bar = CircularProgressBar(
            name="button-mic",
            size=28,
            line_width=2,
            start_angle=150,
            end_angle=390,
        )
        self.mic_label = Label(name="mic-label", markup=icons.mic)
        self.mic_button = Button(on_clicked=self.toggle_mute, child=self.mic_label)
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=Overlay(child=self.progress_bar, overlays=self.mic_button),
        )
        self.audio.connect("notify::microphone", self.on_new_microphone)
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.add(self.event_box)
        self.on_microphone_changed()

    def on_new_microphone(self, *args):
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
            self.on_microphone_changed()

    def toggle_mute(self, event):
        current_stream = self.audio.microphone
        if current_stream:
            current_stream.muted = not current_stream.muted
            if current_stream.muted:
                self.mic_button.get_child().set_markup(icons.mic_mute)
                self.progress_bar.add_style_class("muted")
                self.mic_label.add_style_class("muted")
            else:
                self.on_microphone_changed()
                self.progress_bar.remove_style_class("muted")
                self.mic_label.remove_style_class("muted")

    def on_scroll(self, _, event):
        if not self.audio.microphone:
            return
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if abs(event.delta_y) > 0:
                self.audio.microphone.volume -= event.delta_y
            if abs(event.delta_x) > 0:
                self.audio.microphone.volume += event.delta_x

    def on_microphone_changed(self, *_):
        if not self.audio.microphone:
            return
        if self.audio.microphone.muted:
            self.mic_button.get_child().set_markup(icons.mic_mute)
            self.progress_bar.add_style_class("muted")
            self.mic_label.add_style_class("muted")
            self.set_tooltip_text("Muted")
            return
        else:
            self.progress_bar.remove_style_class("muted")
            self.mic_label.remove_style_class("muted")
        self.progress_bar.value = self.audio.microphone.volume / 100
        self.set_tooltip_text(f"{round(self.audio.microphone.volume)}%")
        if self.audio.microphone.volume >= 1:
            self.mic_button.get_child().set_markup(icons.mic)
        else:
            self.mic_button.get_child().set_markup(icons.mic_mute)


class BrightnessIcon(Box):
    def __init__(self, **kwargs):
        super().__init__(name="brightness-icon", **kwargs)
        self.brightness = Brightness.get_initial()

        self.brightness_label = Label(
            name="brightness-label-dash",
            markup=icons.brightness_high,
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
        )
        self.brightness_button = Button(
            child=self.brightness_label,
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
        )
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=self.brightness_button,
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
        )
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)

        self._pending_value = None
        self._update_source_id = None
        self._updating_from_brightness = False

        self.brightness.connect("screen", self.on_brightness_changed)
        self.on_brightness_changed()
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)

    def on_scroll(self, _, event):
        if self.brightness.max_screen <= 0:
            return

        step_size = 5
        current_brightness = self.brightness.screen_brightness

        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if event.delta_y < 0:
                new_brightness = min(
                    current_brightness + step_size, self.brightness.max_screen
                )
            elif event.delta_y > 0:
                new_brightness = max(current_brightness - step_size, 0)
            else:
                return
        else:
            if event.direction == Gdk.ScrollDirection.UP:
                new_brightness = min(
                    current_brightness + step_size, self.brightness.max_screen
                )
            elif event.direction == Gdk.ScrollDirection.DOWN:
                new_brightness = max(current_brightness - step_size, 0)
            else:
                return

        self._pending_value = new_brightness
        if self._update_source_id is None:
            self._update_source_id = GLib.timeout_add(
                50, self._update_brightness_callback
            )

    def _update_brightness_callback(self):
        if (
            self._pending_value is not None
            and self._pending_value != self.brightness.screen_brightness
        ):
            self.brightness.screen_brightness = self._pending_value
            self._pending_value = None
            return True
        else:
            self._update_source_id = None
            return False

    def on_brightness_changed(self, *args):
        if self.brightness.max_screen <= 0:
            return

        self._updating_from_brightness = True
        normalized = self.brightness.screen_brightness / self.brightness.max_screen
        brightness_percentage = int(normalized * 100)

        if brightness_percentage >= 75:
            self.brightness_label.set_markup("󰃠")
        elif brightness_percentage >= 24:
            self.brightness_label.set_markup("󰃠")
        else:
            self.brightness_label.set_markup("󰃠")
        self.set_tooltip_text(f"{brightness_percentage}%")
        self._updating_from_brightness = False

    def destroy(self):
        if self._update_source_id is not None:
            GLib.source_remove(self._update_source_id)
        super().destroy()


class VolumeIcon(Box):
    def __init__(self, **kwargs):
        super().__init__(name="vol-icon", **kwargs)
        self.audio = Audio()

        self.vol_label = Label(
            name="vol-label-dash",
            markup="",
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
        )
        self.vol_button = Button(
            on_clicked=self.toggle_mute,
            child=self.vol_label,
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
        )

        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=self.vol_button,
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
        )
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)

        self._pending_value = None
        self._update_source_id = None
        self._periodic_update_source_id = None

        self.audio.connect("notify::speaker", self.on_new_speaker)
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)

        self._periodic_update_source_id = GLib.timeout_add_seconds(
            1, self.update_device_icon
        )
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)

    def on_scroll(self, _, event):
        if not self.audio.speaker:
            return

        step_size = 5
        current_volume = self.audio.speaker.volume

        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if event.delta_y < 0:
                new_volume = min(current_volume + step_size, 100)
            elif event.delta_y > 0:
                new_volume = max(current_volume - step_size, 0)
            else:
                return
        else:
            if event.direction == Gdk.ScrollDirection.UP:
                new_volume = min(current_volume + step_size, 100)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                new_volume = max(current_volume - step_size, 0)
            else:
                return

        self._pending_value = new_volume
        if self._update_source_id is None:
            self._update_source_id = GLib.timeout_add(50, self._update_volume_callback)

    def _update_volume_callback(self):
        if (
            self._pending_value is not None
            and self._pending_value != self.audio.speaker.volume
        ):
            self.audio.speaker.volume = self._pending_value
            self._pending_value = None
            return True
        else:
            self._update_source_id = None
            return False

    def on_new_speaker(self, *args):
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
            self.on_speaker_changed()

    def toggle_mute(self, event):
        current_stream = self.audio.speaker
        if current_stream:
            current_stream.muted = not current_stream.muted

            self.on_speaker_changed()

    def on_speaker_changed(self, *_):
        if not self.audio.speaker:
            self.vol_label.set_markup("")
            self.remove_style_class("muted")
            self.vol_label.remove_style_class("muted")
            self.vol_button.remove_style_class("muted")
            self.set_tooltip_text("No audio device")
            return

        if self.audio.speaker.muted:
            self.vol_label.set_markup(icons.headphones)
            self.add_style_class("muted")
            self.vol_label.add_style_class("muted")
            self.vol_button.add_style_class("muted")
            self.set_tooltip_text("Muted")
        else:
            self.remove_style_class("muted")
            self.vol_label.remove_style_class("muted")
            self.vol_button.remove_style_class("muted")

            self.update_device_icon()
            self.set_tooltip_text(f"{round(self.audio.speaker.volume)}%")

    def update_device_icon(self):
        if not self.audio.speaker:
            self.vol_label.set_markup("")

            return True

        if self.audio.speaker.muted:
            return True

        try:
            device_type = self.audio.speaker.port.type
            if device_type == "headphones":
                self.vol_label.set_markup(icons.headphones)
            elif device_type == "speaker":
                self.vol_label.set_markup(icons.headphones)
            else:
                self.vol_label.set_markup(icons.headphones)

        except AttributeError:
            self.vol_label.set_markup(icons.headphones)

        return True

    def destroy(self):
        if self._update_source_id is not None:
            GLib.source_remove(self._update_source_id)

        if (
            hasattr(self, "_periodic_update_source_id")
            and self._periodic_update_source_id is not None
        ):
            GLib.source_remove(self._periodic_update_source_id)
        super().destroy()


class MicIcon(Box):
    def __init__(self, **kwargs):
        super().__init__(name="mic-icon", **kwargs)
        self.audio = Audio()

        self.mic_label = Label(
            name="mic-label-dash",
            markup=icons.mic,
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
        )
        self.mic_button = Button(
            on_clicked=self.toggle_mute,
            child=self.mic_label,
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
        )

        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=self.mic_button,
            h_align="center",
            v_align="center",
            h_expand=True,
            v_expand=True,
        )
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)

        self._pending_value = None
        self._update_source_id = None

        self.audio.connect("notify::microphone", self.on_new_microphone)
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
        self.on_microphone_changed()
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)

    def on_scroll(self, _, event):
        if not self.audio.microphone:
            return

        step_size = 5
        current_volume = self.audio.microphone.volume

        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if event.delta_y < 0:
                new_volume = min(current_volume + step_size, 100)
            elif event.delta_y > 0:
                new_volume = max(current_volume - step_size, 0)
            else:
                return
        else:
            if event.direction == Gdk.ScrollDirection.UP:
                new_volume = min(current_volume + step_size, 100)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                new_volume = max(current_volume - step_size, 0)
            else:
                return

        self._pending_value = new_volume
        if self._update_source_id is None:
            self._update_source_id = GLib.timeout_add(50, self._update_volume_callback)

    def _update_volume_callback(self):
        if (
            self._pending_value is not None
            and self._pending_value != self.audio.microphone.volume
        ):
            self.audio.microphone.volume = self._pending_value
            self._pending_value = None
            return True
        else:
            self._update_source_id = None
            return False

    def on_new_microphone(self, *args):
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
            self.on_microphone_changed()

    def toggle_mute(self, event):
        current_stream = self.audio.microphone
        if current_stream:
            current_stream.muted = not current_stream.muted
            self.on_microphone_changed()

    def on_microphone_changed(self, *_):
        if not self.audio.microphone:
            return
        if self.audio.microphone.muted:
            self.mic_button.get_child().set_markup(icons.mic_mute)
            self.add_style_class("muted")
            self.mic_label.add_style_class("muted")
            self.set_tooltip_text("Muted")
            return
        else:
            self.remove_style_class("muted")
            self.mic_label.remove_style_class("muted")

        self.set_tooltip_text(f"{round(self.audio.microphone.volume)}%")
        if self.audio.microphone.volume >= 1:
            self.mic_button.get_child().set_markup(icons.mic)
        else:
            self.mic_button.get_child().set_markup(icons.mic_mute)

    def destroy(self):
        if self._update_source_id is not None:
            GLib.source_remove(self._update_source_id)
        super().destroy()


class ControlSliders(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-sliders",
            orientation="h",
            spacing=8,
            **kwargs,
        )
        self.brightness = Brightness.get_initial()

        self.brightness_row = Box(
            orientation="h", spacing=0, h_expand=True, h_align="fill"
        )
        self.add(self.brightness_row)

        volume_row = Box(orientation="h", spacing=0, h_expand=True, h_align="fill")
        volume_row.add(VolumeIcon())
        volume_row.add(VolumeSlider())
        self.add(volume_row)

        mic_row = Box(orientation="h", spacing=0, h_expand=True, h_align="fill")
        mic_row.add(MicIcon())
        mic_row.add(MicSlider())
        self.add(mic_row)

        if self.brightness.screen_device:
            self._add_brightness_controls()
        else:
            self.brightness.connect("ready", self._add_brightness_controls)

        self.show_all()

    def _add_brightness_controls(self, *args):
        self.brightness_row.add(BrightnessIcon())
        self.brightness_row.add(BrightnessSlider())
        self.brightness_row.show_all()
        self.reorder_child(self.brightness_row, 0)


class ControlSmall(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-small",
            orientation="h" if not data.VERTICAL else "v",
            spacing=4,
            **kwargs,
        )
        self.brightness = Brightness.get_initial()

        self.add(VolumeSmall())
        self.add(MicSmall())

        if self.brightness.screen_device:
            self._add_brightness_control()
        else:
            self.brightness.connect("ready", self._add_brightness_control)

        self.show_all()

    def _add_brightness_control(self, *args):
        brightness_widget = BrightnessSmall()
        self.pack_start(brightness_widget, False, False, 0)
        self.reorder_child(brightness_widget, 0)
        brightness_widget.show()
