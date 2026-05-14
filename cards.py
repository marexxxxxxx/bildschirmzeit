import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Pango, GLib
import math

class SummaryCard(Gtk.Box):
    def __init__(self, total_seconds):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("card")
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Calculate hours and mins
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60

        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        # Mock icon
        icon = Gtk.Label(label="⏱")
        title = Gtk.Label(label="Total Screen Time")
        title.add_css_class("card-title")
        title_box.append(icon)
        title_box.append(title)
        top_box.append(title_box)

        time_lbl = Gtk.Label(label=f"{int(hours)}h {int(mins)}m", xalign=0)
        time_lbl.add_css_class("display-text")
        top_box.append(time_lbl)

        trend_lbl = Gtk.Label(label="↓ 12% from yesterday", xalign=0)
        trend_lbl.add_css_class("trend-text")
        top_box.append(trend_lbl)

        self.append(top_box)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        self.append(spacer)

        # Bottom Productivity Score
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        bottom_box.set_margin_top(32)

        score_info = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl1 = Gtk.Label(label="Productivity Score", xalign=0)
        lbl1.add_css_class("card-title")
        lbl2 = Gtk.Label(label="78%", xalign=1)
        lbl2.set_hexpand(True)
        lbl2.add_css_class("card-title")
        score_info.append(lbl1)
        score_info.append(lbl2)
        bottom_box.append(score_info)

        # Progress bar
        track = Gtk.Box()
        track.add_css_class("progress-track")
        fill = Gtk.Box()
        fill.add_css_class("progress-fill-primary")
        fill.set_size_request(150, -1) # Mock width for 78%

        track_overlay = Gtk.Overlay()
        track_overlay.set_child(track)
        track_overlay.add_overlay(fill)
        bottom_box.append(track_overlay)

        self.append(bottom_box)

class ChartCard(Gtk.Box):
    def __init__(self, hourly_data):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("card")
        self.set_hexpand(True)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title = Gtk.Label(label="Daily Usage", xalign=0)
        title.add_css_class("card-title-lg")

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        controls.add_css_class("segmented-bg")
        controls.set_halign(Gtk.Align.END)
        controls.set_hexpand(True)
        btn_day = Gtk.Label(label="Day")
        btn_day.add_css_class("segmented-active")
        btn_day.set_margin_start(16)
        btn_day.set_margin_end(16)
        btn_day.set_margin_top(4)
        btn_day.set_margin_bottom(4)
        btn_week = Gtk.Label(label="Week")
        btn_week.add_css_class("segmented-inactive")
        btn_week.set_margin_start(16)
        btn_week.set_margin_end(16)

        controls.append(btn_day)
        controls.append(btn_week)

        header.append(title)
        header.append(controls)
        self.append(header)

        # Chart Area
        chart_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        chart_area.set_vexpand(True)
        chart_area.set_margin_top(24)
        chart_area.set_valign(Gtk.Align.END)
        chart_area.set_size_request(-1, 200)

        # We need to map 6, 9, 12, 15 (3PM), 18 (6PM), 21 (9PM)
        labels = [6, 9, 12, 15, 18, 21]
        display_labels = ["6 AM", "9 AM", "12 PM", "3 PM", "6 PM", "9 PM"]

        max_val = max(hourly_data.values()) if hourly_data else 1
        if max_val == 0: max_val = 1

        chart_area.set_homogeneous(True)

        for i, h in enumerate(labels):
            # Sum data for h, h+1, h+2
            val = hourly_data.get(h, 0) + hourly_data.get(h+1, 0) + hourly_data.get(h+2, 0)
            height_pct = val / max_val

            bar_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            bar_container.set_valign(Gtk.Align.END)
            bar_container.set_hexpand(True)

            bar = Gtk.Box()
            bar.set_size_request(-1, max(10, int(150 * height_pct)))

            hours = int(val // 3600)
            mins = int((val % 3600) // 60)
            dur_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            bar.set_tooltip_text(dur_str)

            lbl = Gtk.Label(label=display_labels[i])
            lbl.add_css_class("chart-label")

            if height_pct == 1.0 and val > 0:
                bar.add_css_class("chart-bar-active")
                lbl.add_css_class("chart-label-active")
            else:
                bar.add_css_class("chart-bar-bg")

            bar_container.append(bar)
            bar_container.append(lbl)
            chart_area.append(bar_container)

        self.append(chart_area)

import os
import urllib.request
import urllib.parse
import threading

def get_icon_name_for_app(app_name, window_class):
    app_name_lower = app_name.lower() if app_name else ""
    window_class_lower = window_class.lower() if window_class else ""

    mapping = {
        "code": "visual-studio-code",
        "vs code": "visual-studio-code",
        "cursor": "cursor",
        "google chrome": "google-chrome",
        "chrome": "google-chrome",
        "firefox": "firefox",
        "slack": "slack",
        "discord": "discord",
        "spotify": "spotify",
        "youtube": "youtube",
        "kitty": "kitty",
        "alacritty": "alacritty",
        "safari": "safari",
        "terminal": "utilities-terminal",
        "settings": "preferences-system"
    }

    # 1. First check mapping based on app_name (e.g. "YouTube")
    if app_name_lower in mapping:
        return mapping[app_name_lower]

    for key, val in mapping.items():
        if key in app_name_lower:
            return val

    # 2. Then check system icon theme for app_name
    try:
        display = Gdk.Display.get_default()
        if display:
            theme = Gtk.IconTheme.get_for_display(display)
            if app_name and theme.has_icon(app_name_lower):
                return app_name_lower
    except Exception:
        pass

    # 3. Check system icon theme for window_class
    try:
        display = Gdk.Display.get_default()
        if display:
            theme = Gtk.IconTheme.get_for_display(display)
            if window_class and theme.has_icon(window_class):
                return window_class
            if window_class and theme.has_icon(window_class_lower):
                return window_class_lower
    except Exception:
        pass

    # Check mapping based on window_class as fallback
    if window_class_lower in mapping:
        return mapping[window_class_lower]

    # Default fallback
    return "application-x-executable"

def download_favicon(app_name, filepath, image_widget):
    domain = f"{app_name.lower().replace(' ', '')}.com"
    url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req).read()

        # Google favicons might return a default globe icon if not found.
        # We can try to save it anyway, as it's better than nothing,
        # or we could check the file size (default is usually small and specific).
        # We will save it if it's > 0 bytes.
        if data:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(data)

            # Update the UI on the main thread
            GLib.idle_add(update_image_widget, image_widget, filepath)
    except Exception as e:
        print(f"Failed to download icon for {app_name}: {e}")

def update_image_widget(image_widget, filepath):
    try:
        image_widget.set_from_file(filepath)
        image_widget.set_pixel_size(32)
    except Exception:
        pass
    return False

def create_app_icon(app_name, window_class):
    image_widget = Gtk.Image()
    image_widget.set_pixel_size(32)
    image_widget.add_css_class("app-icon")

    # 1. Try to get a native or mapped icon first (high quality)
    icon_name = get_icon_name_for_app(app_name, window_class)

    # If the icon name is a generic fallback and we have an app_name, try to get a favicon
    # Or if we want favicons for web apps even if they are in the mapping (like youtube)
    # The user specifically requested "nutzte die icons die im chrome tab stehen"
    # So we should prioritize the favicon if the window_class indicates it's a browser, or always try for specific names.

    is_browser = window_class and window_class.lower() in ["google-chrome", "firefox", "brave-browser", "safari", "chromium"]

    if is_browser and app_name:
        icons_dir = os.path.expanduser("~/.local/share/window_monitor/icons")
        safe_app_name = "".join([c for c in app_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        filepath = os.path.join(icons_dir, f"{safe_app_name.replace(' ', '_').lower()}.png")

        if os.path.exists(filepath):
            image_widget.set_from_file(filepath)
            return image_widget
        else:
            # Set fallback while downloading
            image_widget.set_from_icon_name(icon_name)

            # Start background download
            threading.Thread(target=download_favicon, args=(app_name, filepath, image_widget), daemon=True).start()
            return image_widget

    # If not a browser or no app_name, just use the local icon
    image_widget.set_from_icon_name(icon_name)
    return image_widget

class AppsCard(Gtk.Box):
    def __init__(self, apps_data):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.add_css_class("card")
        self.set_hexpand(True)

        title = Gtk.Label(label="Most Used", xalign=0)
        title.add_css_class("card-title-lg")
        self.append(title)

        # Filter apps with duration > 120 seconds
        top_apps = [app for app in apps_data if app[1] > 120]

        if not top_apps:
            self.set_visible(False)
            return

        max_duration = top_apps[0][1] if top_apps else 1

        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)

        colors = ["progress-fill-primary", "progress-fill-safari", "progress-fill-tertiary"]
        bg_colors = ["#000000", "#0070eb", "#4A154B"]

        for i, app_data in enumerate(top_apps):
            app_name = app_data[0]
            duration = app_data[1]
            window_class = app_data[2] if len(app_data) > 2 else None

            app_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

            info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

            # System Icon or Downloaded Favicon
            app_icon = create_app_icon(app_name, window_class)

            name_lbl = Gtk.Label(label=app_name)
            name_lbl.add_css_class("app-name")
            name_lbl.set_margin_start(12)

            h = int(duration // 3600)
            m = int((duration % 3600) // 60)
            time_str = f"{h}h {m}m" if h > 0 else f"{m}m"

            time_lbl = Gtk.Label(label=time_str, xalign=1)
            time_lbl.add_css_class("app-duration")
            time_lbl.set_hexpand(True)

            info_box.append(app_icon)
            info_box.append(name_lbl)
            info_box.append(time_lbl)

            app_box.append(info_box)

            # Progress bar
            track = Gtk.Box()
            track.add_css_class("progress-track")
            fill = Gtk.Box()
            fill.add_css_class(colors[i % len(colors)])
            width_pct = max(0.05, duration / max_duration)
            # Rough approximation since we can't easily set percentage width in GTK boxes without a custom layout manager
            fill.set_size_request(int(250 * width_pct), -1)

            track_overlay = Gtk.Overlay()
            track_overlay.set_child(track)
            track_overlay.add_overlay(fill)

            app_box.append(track_overlay)
            list_box.append(app_box)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(list_box)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_vexpand(True)
        scrolled_window.set_min_content_height(200)

        self.append(scrolled_window)

class CategoriesCard(Gtk.Box):
    def __init__(self, categories_data):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.add_css_class("card")
        self.set_hexpand(True)

        title = Gtk.Label(label="Categories", xalign=0)
        title.add_css_class("card-title-lg")
        self.append(title)

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=32)
        content.set_vexpand(True)

        # Donut Chart
        self.cat_data = categories_data
        chart_area = Gtk.DrawingArea()
        chart_area.set_size_request(128, 128)
        chart_area.set_draw_func(self.draw_donut)
        content.append(chart_area)

        # Legend
        legend = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        legend.set_valign(Gtk.Align.CENTER)
        legend.set_hexpand(True)

        mapping = [
            ("Productivity", "legend-dot-primary"),
            ("Communication", "legend-dot-secondary"),
            ("Entertainment", "legend-dot-tertiary")
        ]

        for name, cls in mapping:
            pct = self.cat_data.get(name, 0)
            if pct == 0 and name != "Productivity": # keep at least one if empty to match mockup
                continue

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            dot = Gtk.Box()
            dot.add_css_class(cls)
            dot.set_valign(Gtk.Align.CENTER)

            lbl = Gtk.Label(label=name)
            lbl.add_css_class("legend-label")

            val = Gtk.Label(label=f"{int(pct)}%", xalign=1)
            val.add_css_class("legend-value")
            val.set_hexpand(True)

            row.append(dot)
            row.append(lbl)
            row.append(val)
            legend.append(row)

        content.append(legend)
        self.append(content)

    def draw_donut(self, area, cr, width, height):
        xc = width / 2.0
        yc = height / 2.0
        radius = min(width, height) / 2.0 - 10

        # Background track
        cr.set_line_width(16)
        cr.arc(xc, yc, radius, 0, 2 * math.pi)
        cr.set_source_rgba(0.91, 0.9, 0.93, 1.0) # surface-container-high
        cr.stroke()

        colors = {
            "Productivity": (0.0, 0.345, 0.737), # primary
            "Communication": (0.0, 0.431, 0.157), # secondary
            "Entertainment": (0.298, 0.29, 0.792), # tertiary
        }

        current_angle = -math.pi / 2.0 # Start at 12 o'clock

        for name, color in colors.items():
            pct = self.cat_data.get(name, 0) / 100.0
            if pct <= 0:
                continue

            angle = pct * 2 * math.pi

            cr.set_source_rgb(*color)
            cr.arc(xc, yc, radius, current_angle, current_angle + angle)
            cr.stroke()

            current_angle += angle
