import gi
import sys
import argparse
import subprocess
import json
import logging
import os

gi.require_version('Gtk', '4.0')
try:
    gi.require_version('Gtk4LayerShell', '1.0')
    from gi.repository import Gtk4LayerShell
except ValueError:
    Gtk4LayerShell = None
    logging.warning("Gtk4LayerShell not found. Ensure it is installed on the target system.")

from gi.repository import Gtk, GLib, Gdk, Gio, Pango

def get_window_info(title_substring):
    try:
        res = subprocess.run(['hyprctl', 'clients', '-j'], capture_output=True, text=True)
        if res.returncode == 0:
            clients = json.loads(res.stdout)
            for c in clients:
                if title_substring.lower() in c.get('title', '').lower():
                    at = c.get('at', [0, 0])
                    size = c.get('size', [0, 0])
                    return {
                        'x': int(at[0]),
                        'y': int(at[1]),
                        'width': int(size[0]),
                        'height': int(size[1])
                    }
    except Exception as e:
        logging.error(f"Fehler beim Auslesen der Fensterinfo: {e}")
    return None

class BlockerOverlay(Gtk.Window):
    def __init__(self, app, title_substring, image_path=None):
        super().__init__(application=app)
        self.title_substring = title_substring

        info = get_window_info(self.title_substring)
        if not info:
            logging.error(f"Fenster mit Titel '{self.title_substring}' nicht gefunden.")
            x, y, w, h = 0, 0, 800, 600
        else:
            x, y, w, h = info['x'], info['y'], info['width'], info['height']

        if Gtk4LayerShell is not None:
            Gtk4LayerShell.init_for_window(self)
            Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.OVERLAY)
            # You must anchor the window to LEFT and TOP to use margins as offsets
            Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.LEFT, True)
            Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.TOP, True)
            Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.LEFT, x)
            Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.TOP, y)
            Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.ON_DEMAND)
        else:
            logging.warning("Gtk4LayerShell is not available. Falling back to normal window.")

        self.set_default_size(w, h)
        self.set_decorated(False)

        # Main box. We use this to set the size request dynamically.
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # In GTK4, set_size_request on the child controls the actual window size
        # (especially allowing it to shrink) when using Layer Shell
        self.box.set_size_request(w, h)
        self.set_child(self.box)

        if image_path:
            img = Gtk.Image.new_from_file(image_path)
            self.box.append(img)
            # Append close button just in case there's an image
            btn = Gtk.Button(label="× Freigeben")
            btn.set_margin_top(10)
            btn.set_margin_bottom(10)
            btn.set_halign(Gtk.Align.CENTER)
            btn.connect('clicked', lambda _: self.close_overlay(app))
            self.box.append(btn)
        else:
            # Use Cairo standard layout as requested
            area = Gtk.DrawingArea()
            area.set_draw_func(self.on_draw, None)
            area.set_vexpand(True) # Take up all vertical space except the button
            self.box.append(area)

            # Center a button box at the bottom
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            btn_box.set_halign(Gtk.Align.CENTER)
            btn_box.set_margin_bottom(20)

            # Styling for buttons to look somewhat like the user's design
            css_provider = Gtk.CssProvider()
            css_data = """
            .btn-ignore {
                background-color: #E5E5EA;
                color: black;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 16px;
                border: none;
            }
            .btn-ok {
                background-color: #007AFF;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 16px;
                border: none;
            }
            """
            css_provider.load_from_string(css_data)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

            btn_ignore = Gtk.Button(label="Ignore Limit")
            btn_ignore.add_css_class("btn-ignore")
            btn_ignore.connect('clicked', lambda _: self.close_overlay(app))

            btn_ok = Gtk.Button(label="OK")
            btn_ok.add_css_class("btn-ok")
            btn_ok.connect('clicked', lambda _: self.close_overlay(app))

            btn_box.append(btn_ignore)
            btn_box.append(btn_ok)

            self.box.append(btn_box)

        # Polling setup for updating position/size
        GLib.timeout_add(500, self.update_geometry)

    def on_draw(self, area, cr, width, height, data):
        # White background
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.95)
        cr.paint()

        # Draw Hourglass Icon (simple representation using shapes or text)
        # Here we use text since it's reliable across environments without external assets
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 1) # bold

        # Center texts
        # Title
        cr.set_font_size(32)
        title = "Time Limit Reached"
        text_extents = cr.text_extents(title)
        cr.move_to(width/2 - text_extents.width/2, height/2 - 20)
        cr.show_text(title)

        # Subtitle
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.select_font_face("Sans", 0, 0) # normal
        cr.set_font_size(18)
        subtitle = "You've reached your limit for Social Media."
        sub_extents = cr.text_extents(subtitle)
        cr.move_to(width/2 - sub_extents.width/2, height/2 + 20)
        cr.show_text(subtitle)

        # Basic hourglass drawing (two triangles)
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(4)

        hx, hy = width/2, height/2 - 100
        size = 30

        # Top triangle
        cr.move_to(hx - size, hy - size)
        cr.line_to(hx + size, hy - size)
        cr.line_to(hx, hy)
        cr.close_path()
        cr.stroke()

        # Bottom triangle
        cr.move_to(hx, hy)
        cr.line_to(hx - size, hy + size)
        cr.line_to(hx + size, hy + size)
        cr.close_path()
        cr.fill()

        # Top and bottom bars
        cr.move_to(hx - size - 5, hy - size)
        cr.line_to(hx + size + 5, hy - size)
        cr.stroke()

        cr.move_to(hx - size - 5, hy + size)
        cr.line_to(hx + size + 5, hy + size)
        cr.stroke()

    def close_overlay(self, app):
        self.destroy()
        app.quit()

    def update_geometry(self):
        info = get_window_info(self.title_substring)
        if info:
            if Gtk4LayerShell is not None:
                Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.LEFT, info['x'])
                Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.TOP, info['y'])
            # Set size request on the box to allow shrinking
            self.box.set_size_request(info['width'], info['height'])
            # Also call set_default_size for the window itself
            self.set_default_size(info['width'], info['height'])
        return True # Keep polling

class BlockerApplication(Gtk.Application):
    def __init__(self, title, image_path):
        super().__init__(application_id='org.omarchy.blockeroverlay', flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.title_to_block = title
        self.image_path = image_path

    def do_activate(self):
        win = BlockerOverlay(self, self.title_to_block, self.image_path)
        win.present()

def main():
    parser = argparse.ArgumentParser(description="Overlay Blocker for Hyprland")
    parser.add_argument("--title", required=True, help="Titel des zu blockierenden Fensters")
    parser.add_argument("--image", help="Optionaler Pfad zu einem Bild für das Overlay", default=None)
    args = parser.parse_args()

    app = BlockerApplication(args.title, args.image)
    app.run(None)

if __name__ == '__main__':
    main()
