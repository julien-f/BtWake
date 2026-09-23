#!/usr/bin/env python3
"""Render the app with fake devices to data/screenshots/main.png.

Uses made-up devices so real MAC addresses don't end up in the repository.
Usage: tools/screenshot.py [output.png]
"""

import importlib.machinery
import importlib.util
import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Graphene, Gtk  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "screenshots", "main.png")

loader = importlib.machinery.SourceFileLoader("bt_wake", os.path.join(ROOT, "bt-wake"))
spec = importlib.util.spec_from_loader("bt_wake", loader)
app_mod = importlib.util.module_from_spec(spec)
loader.exec_module(app_mod)


def device(alias, address, icon, connected, wake=None):
    props = {"Alias": alias, "Address": address, "Icon": icon, "Paired": True, "Connected": connected}
    if wake is not None:
        props["WakeAllowed"] = wake
    return {app_mod.DEVICE_IFACE: props}


FAKE_OBJECTS = {
    "/org/bluez/hci0": {app_mod.ADAPTER_IFACE: {"Powered": True}},
    "/org/bluez/hci0/dev_1": device("MX Anywhere 3S", "C4:2F:90:1A:7E:31", "input-mouse", True, wake=False),
    "/org/bluez/hci0/dev_2": device("Keychron K3", "DC:2C:26:5B:04:9A", "input-keyboard", True, wake=True),
    "/org/bluez/hci0/dev_3": device("WH-1000XM4", "38:18:4C:D2:61:0F", "audio-headphones", True),
    "/org/bluez/hci0/dev_4": device("8BitDo Pro 2", "E4:17:D8:3C:88:B2", "input-gaming", False, wake=False),
    "/org/bluez/hci0/dev_5": device("Pixel 8", "A4:C3:F0:57:19:6D", "phone", False),
}


class FakeResult:
    def unpack(self):
        return (FAKE_OBJECTS,)


class FakeBus:
    def call_sync(self, *_args):
        return FakeResult()

    def signal_subscribe(self, *_args):
        return 0


# Swap the system bus and sysfs check for fakes before any window is built.
app_mod.Gio.bus_get_sync = lambda *_: FakeBus()
app_mod.controller_can_wake = lambda _hci: True


def capture(window):
    width, height = window.get_width(), window.get_height()
    snapshot = Gtk.Snapshot()
    Gtk.WidgetPaintable(widget=window).snapshot(snapshot, width, height)
    node = snapshot.to_node()
    bounds = Graphene.Rect().init(0, 0, width, height)
    texture = window.get_renderer().render_texture(node, bounds)
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    texture.save_to_png(OUTPUT)
    print(f"Saved {OUTPUT} ({width}x{height})")
    window.get_application().quit()
    return GLib.SOURCE_REMOVE


class ScreenshotApp(app_mod.App):
    def do_activate(self):
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        window = app_mod.Window(self)
        window.set_default_size(460, 440)
        window.present()
        GLib.timeout_add(1000, capture, window)


if __name__ == "__main__":
    sys.exit(ScreenshotApp().run([sys.argv[0]]))
