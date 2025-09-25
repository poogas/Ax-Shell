import math
import gi
from fabric.audio.service import Audio
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.scale import Scale
from fabric.widgets.scrolledwindow import ScrolledWindow
from gi.repository import GLib

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import config.data as data

vertical_mode = (
    True
    if data.PANEL_THEME == "Panel"
    and (
        data.BAR_POSITION in ["Left", "Right"]
        or data.PANEL_POSITION in ["Start", "End"]
    )
    else False
)


class MixerSlider(Scale):
    def __init__(self, stream, label, **kwargs):
        super().__init__(
            name="control-slider",
            orientation="h",
            h_expand=True,
            h_align="fill",
            has_origin=True,
            increments=(0.01, 0.1),
            style_classes=["no-icon"],
            **kwargs,
        )

        self.stream = stream
        self.label = label
        self._updating_from_stream = False
        self.set_value(stream.volume / 100)

        self.stream_handler_id = stream.connect("changed", self.on_stream_changed)
        self.connect("value-changed", self.on_value_changed)
        self.connect("destroy", self.on_destroy)

        if hasattr(stream, "type"):
            if "microphone" in stream.type.lower() or "input" in stream.type.lower():
                self.add_style_class("mic")
            else:
                self.add_style_class("vol")
        else:
            self.add_style_class("vol")

        self.set_tooltip_text(f"{stream.volume:.0f}%")
        self.update_muted_state()

    def on_destroy(self, *args):
        if self.stream and self.stream_handler_id > 0:
            self.stream.disconnect(self.stream_handler_id)
            self.stream_handler_id = 0

    def on_value_changed(self, _):
        if self._updating_from_stream:
            return
        if self.stream:
            self.stream.volume = self.value * 100
            self.set_tooltip_text(f"{self.value * 100:.0f}%")

    def on_stream_changed(self, stream):
        self._updating_from_stream = True
        self.value = stream.volume / 100
        self.set_tooltip_text(f"{stream.volume:.0f}%")
        self.update_muted_state()

        if self.label:
            self.label.set_label(f"[{math.ceil(stream.volume)}%] {stream.description}")
        self._updating_from_stream = False

    def update_muted_state(self):
        if self.stream.muted:
            self.add_style_class("muted")
        else:
            self.remove_style_class("muted")

class MixerSection(Box):
    def __init__(self, title, **kwargs):
        super().__init__(
            name="mixer-section",
            orientation="v",
            spacing=8,
            h_expand=True,
            v_expand=True,
        )

        self.title_label = Label(
            name="mixer-section-title",
            label=title,
            h_expand=True,
            h_align="fill",
        )

        self.content_box = Box(
            name="mixer-content",
            orientation="v",
            spacing=8,
            h_expand=True,
            v_expand=True,
        )

        self.add(self.title_label)
        self.add(self.content_box)

    def update_streams(self, streams):
        self.content_box.freeze_child_notify()

        for child in self.content_box.get_children():
            self.content_box.remove(child)

        for stream in streams:
            stream_container = Box(
                orientation="v",
                spacing=4,
                h_expand=True,
                v_align="center",
            )

            label = Label(
                name="mixer-stream-label",
                label=f"[{math.ceil(stream.volume)}%] {stream.description}",
                h_expand=True,
                h_align="start",
                v_align="center",
                ellipsization="end",
                max_chars_width=45,
            )
            
            slider = MixerSlider(stream, label)

            stream_container.add(label)
            stream_container.add(slider)
            self.content_box.add(stream_container)

        self.content_box.thaw_child_notify()
        self.content_box.show_all()

class Mixer(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="mixer",
            orientation="v",
            spacing=8,
            h_expand=True,
            v_expand=True,
        )

        self._output_stream_names = set()
        self._input_stream_names = set()
        self._update_pending = False

        try:
            self.audio = Audio()
        except Exception as e:
            error_label = Label(
                label=f"Audio service unavailable: {str(e)}",
                h_align="center",
                v_align="center",
                h_expand=True,
                v_expand=True,
            )
            self.add(error_label)
            return

        self.main_container = Box(
            orientation="h" if not vertical_mode else "v",
            spacing=8,
            h_expand=True,
            v_expand=True,
        )

        self.main_container.set_homogeneous(True)
        self.outputs_section = MixerSection("Outputs")
        self.inputs_section = MixerSection("Inputs")
        self.main_container.add(self.outputs_section)
        self.main_container.add(self.inputs_section)

        self.scrolled = ScrolledWindow(
            h_expand=True,
            v_expand=True,
            child=self.main_container,
        )
        self.add(self.scrolled)

        self.audio.connect("changed", self.on_audio_changed)
        self.audio.connect("stream-added", self.on_audio_changed)
        self.audio.connect("stream-removed", self.on_audio_changed)
        
        self.schedule_update()

    def schedule_update(self):
        if not self._update_pending:
            self._update_pending = True
            GLib.idle_add(self.update_mixer)

    def on_audio_changed(self, *args):
        outputs = []
        if self.audio.speaker:
            outputs.append(self.audio.speaker)
        outputs.extend(self.audio.applications or [])

        inputs = []
        if self.audio.microphone:
            inputs.append(self.audio.microphone)
        inputs.extend(self.audio.recorders or [])

        current_output_names = {stream.name for stream in outputs}
        current_input_names = {stream.name for stream in inputs}

        if (current_output_names != self._output_stream_names or
            current_input_names != self._input_stream_names):
            self.schedule_update()
    
    def update_mixer(self):
        outputs = []
        if self.audio.speaker:
            outputs.append(self.audio.speaker)
        outputs.extend(self.audio.applications or [])

        inputs = []
        if self.audio.microphone:
            inputs.append(self.audio.microphone)
        inputs.extend(self.audio.recorders or [])
        
        outputs.sort(key=lambda s: s.description)
        inputs.sort(key=lambda s: s.description)
        
        self._output_stream_names = {stream.name for stream in outputs}
        self._input_stream_names = {stream.name for stream in inputs}

        self.outputs_section.update_streams(outputs)
        self.inputs_section.update_streams(inputs)
        
        self._update_pending = False
        return False
