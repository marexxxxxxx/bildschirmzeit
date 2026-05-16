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
    def __init__(self, weekly_data):
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
        btn_day.add_css_class("segmented-inactive")
        btn_day.set_margin_start(16)
        btn_day.set_margin_end(16)
        btn_day.set_margin_top(4)
        btn_day.set_margin_bottom(4)
        btn_week = Gtk.Label(label="Week")
        btn_week.add_css_class("segmented-active")
        btn_week.set_margin_start(16)
        btn_week.set_margin_end(16)

        controls.append(btn_day)
        controls.append(btn_week)

        header.append(title)
        header.append(controls)
        self.append(header)

        # Chart Grid Container
        chart_grid_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        chart_grid_container.set_vexpand(True)
        chart_grid_container.set_margin_top(24)
        chart_grid_container.set_margin_bottom(16)

        # For a 200px tall chart representing 8h, we want 5 labels at 0, 50, 100, 150, 200 px.
        # We can achieve this precise positioning using a vertical box with spacing or an overlay.
        # Let's use a standard VBox with 4 homogeneous expanded sections for both the labels and grid.

        # Left Y-Axis labels
        y_axis_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        y_axis_box.set_size_request(24, 200)
        y_axis_labels = ["8h", "6h", "4h", "2h", "0h"]

        for i, lbl_text in enumerate(y_axis_labels):
            lbl = Gtk.Label(label=lbl_text, xalign=1)
            lbl.add_css_class("y-axis-label")
            # The top label aligns to top, bottom to bottom, rest inside expanded space
            if i == 0:
                y_axis_box.append(lbl)
            else:
                # Create a filler box that pushes the next label down
                filler = Gtk.Box()
                filler.set_vexpand(True)
                y_axis_box.append(filler)
                y_axis_box.append(lbl)

        chart_grid_container.append(y_axis_box)

        # Right Chart Area Overlay
        chart_overlay = Gtk.Overlay()
        chart_overlay.set_hexpand(True)
        chart_overlay.set_size_request(-1, 200)

        # 1. Background Grid Lines (dividing height into 4 sections)
        grid_lines_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Top line
        top_line = Gtk.Box()
        top_line.set_hexpand(True)
        top_line.add_css_class("chart-grid-row")
        grid_lines_box.append(top_line)

        # Next 3 lines with expanders
        for i in range(3):
            filler = Gtk.Box()
            filler.set_vexpand(True)
            grid_lines_box.append(filler)

            line = Gtk.Box()
            line.set_hexpand(True)
            line.add_css_class("chart-grid-row")
            grid_lines_box.append(line)

        # Bottom line
        filler = Gtk.Box()
        filler.set_vexpand(True)
        grid_lines_box.append(filler)

        bottom_line = Gtk.Box()
        bottom_line.set_hexpand(True)
        bottom_line.add_css_class("chart-grid-row")
        grid_lines_box.append(bottom_line)

        chart_overlay.set_child(grid_lines_box)

        # 2. Foreground Bars
        chart_bars_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        chart_bars_box.set_homogeneous(True)

        display_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        # Determine maximum total time for any day to scale appropriately. Base 8 hours (28800 seconds).
        max_total_sec = 8 * 3600
        for i in range(7):
            day_data = weekly_data.get(i, {})
            day_total = sum(day_data.values())
            if day_total > max_total_sec:
                max_total_sec = day_total

        if max_total_sec == 0:
            max_total_sec = 1

        chart_height = 200

        for i in range(7):
            day_data = weekly_data.get(i, {})

            bar_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            bar_container.set_valign(Gtk.Align.END)
            bar_container.set_halign(Gtk.Align.CENTER)
            bar_container.set_hexpand(True)

            # Stacked Bar
            stacked_bar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            stacked_bar.add_css_class("stacked-bar-container")
            stacked_bar.set_size_request(24, -1) # Width of the bar

            # The order in VBox from top to bottom is important.
            # Visually, we want Productivity at bottom, Communication middle, Entertainment top.
            # So in a VBox, we add Entertainment first, then Communication, then Productivity.
            categories_order = [
                ("Entertainment", "chart-bar-entertainment"),
                ("Communication", "chart-bar-communication"),
                ("Productivity", "chart-bar-productivity")
            ]

            day_total = sum(day_data.values())

            for cat_name, css_class in categories_order:
                val = day_data.get(cat_name, 0)
                if val > 0:
                    height_pct = val / max_total_sec
                    segment_height = max(4, int(chart_height * height_pct)) # Give minimum height
                    segment = Gtk.Box()
                    segment.add_css_class(css_class)
                    segment.set_size_request(-1, segment_height)
                    stacked_bar.append(segment)

            # If no data, add an empty placeholder to keep layout consistent
            if day_total == 0:
                empty_segment = Gtk.Box()
                empty_segment.set_size_request(-1, 0)
                stacked_bar.append(empty_segment)

            lbl = Gtk.Label(label=display_labels[i])
            lbl.add_css_class("chart-label")
            lbl.set_margin_top(8)

            bar_container.append(stacked_bar)
            bar_container.append(lbl)

            chart_bars_box.append(bar_container)

        chart_overlay.add_overlay(chart_bars_box)

        chart_grid_container.append(chart_overlay)
        self.append(chart_grid_container)

        # Legend
        legend_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        legend_box.set_halign(Gtk.Align.CENTER)
        legend_box.set_margin_top(8)

        legend_items = [
            ("Productivity", "chart-bar-productivity"),
            ("Communication", "chart-bar-communication"),
            ("Entertainment", "chart-bar-entertainment")
        ]

        for name, css_class in legend_items:
            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            item_box.set_valign(Gtk.Align.CENTER)

            dot = Gtk.Box()
            dot.add_css_class("legend-dot")
            dot.add_css_class(css_class)
            dot.set_size_request(10, 10)

            lbl = Gtk.Label(label=name)
            lbl.add_css_class("legend-label")

            item_box.append(dot)
            item_box.append(lbl)
            legend_box.append(item_box)

        self.append(legend_box)

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

class ProductivityScoreCard(Gtk.Box):
    def __init__(self, score_pct, focus_seconds):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("card")
        self.set_hexpand(True)
        self.set_vexpand(True)

        title = Gtk.Label(label="PRODUCTIVITY SCORE", xalign=0)
        title.add_css_class("label-sm")
        self.append(title)

        score_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        score_box.set_margin_top(8)

        score_lbl = Gtk.Label(label=f"{int(score_pct)}%", xalign=0)
        score_lbl.add_css_class("display-text")
        score_lbl.set_name("productivity-score-text")
        score_box.append(score_lbl)

        trend = Gtk.Label(label="↑ +5%")
        trend.add_css_class("trend-text-positive")
        trend.set_valign(Gtk.Align.CENTER)

        # Add background to trend
        trend_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        trend_box.add_css_class("trend-badge-positive")
        trend_box.set_valign(Gtk.Align.CENTER)
        trend_box.append(trend)

        score_box.append(trend_box)
        self.append(score_box)

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        self.append(spacer)

        focus_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        focus_box.set_margin_bottom(8)

        focus_title = Gtk.Label(label="Focus Time", xalign=0)
        focus_title.add_css_class("card-title")

        hours = focus_seconds // 3600
        mins = (focus_seconds % 3600) // 60
        focus_time = Gtk.Label(label=f"{int(hours)}h {int(mins)}m", xalign=1)
        focus_time.add_css_class("card-title")
        focus_time.set_hexpand(True)

        focus_box.append(focus_title)
        focus_box.append(focus_time)
        self.append(focus_box)

        track = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        track.add_css_class("progress-track")
        track.set_size_request(-1, 8)

        fill = Gtk.Box()
        fill.add_css_class("progress-fill-primary")
        fill.set_size_request(-1, 8)
        # Mock focus time progress roughly 75%
        fill.set_hexpand(False)
        fill.set_halign(Gtk.Align.START)
        fill.set_size_request(150, 8)

        track.append(fill)
        self.append(track)


class WorkVsLeisureCard(Gtk.Box):
    def __init__(self, weekly_data):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("card")
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_size_request(600, -1)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        title = Gtk.Label(label="Work vs. Leisure", xalign=0)
        title.add_css_class("card-title-lg")
        header.append(title)

        # Legend
        legend_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        legend_box.set_halign(Gtk.Align.END)
        legend_box.set_hexpand(True)

        legend_items = [
            ("Productive", "legend-dot-primary"),
            ("Neutral", "legend-dot-neutral"),
            ("Leisure", "legend-dot-tertiary")
        ]

        for name, css_class in legend_items:
            item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            item.set_valign(Gtk.Align.CENTER)
            dot = Gtk.Box()
            dot.set_size_request(10, 10)
            dot.add_css_class("legend-dot")
            dot.add_css_class(css_class)
            lbl = Gtk.Label(label=name)
            lbl.add_css_class("legend-label")
            item.append(dot)
            item.append(lbl)
            legend_box.append(item)

        header.append(legend_box)
        self.append(header)

        # Main chart area
        chart_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        chart_area.set_vexpand(True)
        chart_area.set_margin_top(24)

        # We leave y-axis empty in this mockup
        bars_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bars_container.set_homogeneous(True)
        bars_container.set_hexpand(True)

        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

        # Fake data for 5 days
        mock_data = [
            {"prod": 150, "neut": 30, "leisure": 50},
            {"prod": 180, "neut": 40, "leisure": 30},
            {"prod": 120, "neut": 20, "leisure": 80},
            {"prod": 200, "neut": 10, "leisure": 20},
            {"prod": 90, "neut": 60, "leisure": 100},
        ]

        max_val = max([d["prod"] + d["neut"] + d["leisure"] for d in mock_data])

        for i, day in enumerate(days):
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

            # Bar container (bottom aligned)
            bar_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            bar_area.set_vexpand(True)
            bar_area.set_valign(Gtk.Align.END)

            stacked_bar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            stacked_bar.add_css_class("stacked-bar-container")
            stacked_bar.set_halign(Gtk.Align.CENTER)
            stacked_bar.set_size_request(24, -1)

            d = mock_data[i]
            total_h = 160 # max height of bar

            # Calculate heights
            h_leisure = (d["leisure"] / max_val) * total_h
            h_neut = (d["neut"] / max_val) * total_h
            h_prod = (d["prod"] / max_val) * total_h

            # Leisure (top)
            if h_leisure > 0:
                seg = Gtk.Box()
                seg.set_size_request(-1, h_leisure)
                seg.add_css_class("chart-bar-other") # use tertiary color in CSS
                stacked_bar.append(seg)

            # Neutral (middle)
            if h_neut > 0:
                seg = Gtk.Box()
                seg.set_size_request(-1, h_neut)
                seg.add_css_class("chart-bar-neutral") # use surface_dim in CSS
                stacked_bar.append(seg)

            # Productive (bottom)
            if h_prod > 0:
                seg = Gtk.Box()
                seg.set_size_request(-1, h_prod)
                seg.add_css_class("chart-bar-productivity")
                stacked_bar.append(seg)

            bar_area.append(stacked_bar)
            col.append(bar_area)

            lbl = Gtk.Label(label=day)
            lbl.add_css_class("chart-label")
            lbl.set_margin_top(12)
            col.append(lbl)

            bars_container.append(col)

        chart_area.append(bars_container)
        self.append(chart_area)


class ProductivityCategoriesCard(Gtk.Box):
    def __init__(self, categories_data):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.add_css_class("card")
        self.set_hexpand(True)
        self.set_vexpand(True)

        title = Gtk.Label(label="Categories", xalign=0)
        title.add_css_class("card-title-lg")
        self.append(title)

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        # remove background from listbox to blend into card
        list_box.add_css_class("transparent-list")

        # Use provided category data or dummy if empty
        if not categories_data:
            categories_data = [
                ("Coding", 3 * 3600 + 45 * 60, "progress-fill-primary", "code-symbolic"),
                ("Design", 1 * 3600 + 20 * 60, "progress-fill-tertiary", "color-select-symbolic"),
                ("Writing", 45 * 60, "progress-fill-secondary", "accessories-text-editor-symbolic")
            ]

        # Calculate max time for progress bar scaling
        max_time = max([c[1] for c in categories_data]) if categories_data else 1

        for name, seconds, css_class, icon_name in categories_data:
            row = Gtk.ListBoxRow()
            row.set_activatable(False)
            row.set_selectable(False)

            item_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            item_box.set_margin_top(12)
            item_box.set_margin_bottom(12)

            top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

            icon = Gtk.Image(icon_name=icon_name)
            icon.add_css_class("category-icon-bg")

            name_lbl = Gtk.Label(label=name, xalign=0)
            name_lbl.add_css_class("card-title")

            top_box.append(icon)
            top_box.append(name_lbl)

            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            time_str = f"{int(hours)}h {int(mins)}m" if hours > 0 else f"{int(mins)}m"
            time_lbl = Gtk.Label(label=time_str, xalign=1)
            time_lbl.add_css_class("card-title")
            time_lbl.set_hexpand(True)
            top_box.append(time_lbl)

            item_box.append(top_box)

            track = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            track.add_css_class("progress-track")
            track.set_size_request(-1, 6)

            fill = Gtk.Box()
            fill.add_css_class(css_class)
            fill.set_size_request(-1, 6)

            # Simple ratio
            ratio = seconds / max_time
            # Workaround to set width fraction using size request (e.g. max 200px)
            fill.set_size_request(int(200 * ratio), 6)
            fill.set_halign(Gtk.Align.START)
            fill.set_hexpand(False)

            track.append(fill)
            item_box.append(track)

            row.set_child(item_box)
            list_box.append(row)

        self.append(list_box)


class RecentDeepWorkCard(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.add_css_class("card")
        self.set_hexpand(True)
        self.set_vexpand(True)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title = Gtk.Label(label="Recent Deep Work", xalign=0)
        title.add_css_class("card-title-lg")

        view_all = Gtk.Button(label="View All")
        view_all.add_css_class("link-button")
        view_all.set_halign(Gtk.Align.END)
        view_all.set_hexpand(True)

        header.append(title)
        header.append(view_all)
        self.append(header)

        mock_data = [
            ("VS Code Architecture", "09:00 AM - 11:30 AM", "2h 30m", "CODING", "primary"),
            ("Figma UI Kit Update", "01:00 PM - 02:20 PM", "1h 20m", "DESIGN", "tertiary"),
            ("Code Review & PRs", "03:00 PM - 04:15 PM", "1h 15m", "CODING", "primary"),
        ]

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("transparent-list")

        for name, time_range, dur, badge, color_cls in mock_data:
            row = Gtk.ListBoxRow()
            row.set_activatable(False)
            row.set_selectable(False)

            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            item_box.set_margin_top(12)
            item_box.set_margin_bottom(12)

            # Left accent bar
            accent = Gtk.Box()
            accent.set_size_request(4, -1)
            accent.add_css_class(f"bg-{color_cls}")
            accent.add_css_class("rounded")

            item_box.append(accent)

            center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            name_lbl = Gtk.Label(label=name, xalign=0)
            name_lbl.add_css_class("label-md")
            name_lbl.add_css_class("text-on-surface")

            time_lbl = Gtk.Label(label=f"⏱ {time_range}", xalign=0)
            time_lbl.add_css_class("label-sm")

            center_box.append(name_lbl)
            center_box.append(time_lbl)
            center_box.set_hexpand(True)
            item_box.append(center_box)

            right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            dur_lbl = Gtk.Label(label=dur, xalign=1)
            dur_lbl.add_css_class("label-md")
            dur_lbl.add_css_class("text-primary")

            badge_lbl = Gtk.Label(label=badge, xalign=1)
            badge_lbl.add_css_class("badge")

            right_box.append(dur_lbl)
            right_box.append(badge_lbl)
            item_box.append(right_box)

            row.set_child(item_box)
            list_box.append(row)

        self.append(list_box)
