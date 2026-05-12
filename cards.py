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

        for i, h in enumerate(labels):
            # Sum data for h, h+1, h+2
            val = hourly_data.get(h, 0) + hourly_data.get(h+1, 0) + hourly_data.get(h+2, 0)
            height_pct = val / max_val

            bar_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            bar_container.set_valign(Gtk.Align.END)
            bar_container.set_hexpand(True)

            bar = Gtk.Box()
            bar.set_size_request(-1, max(10, int(150 * height_pct)))

            if height_pct == 1.0 and val > 0:
                bar.add_css_class("chart-bar-active")
            else:
                bar.add_css_class("chart-bar-bg")

            lbl = Gtk.Label(label=display_labels[i])
            lbl.add_css_class("chart-label")

            bar_container.append(bar)
            bar_container.append(lbl)
            chart_area.append(bar_container)

        self.append(chart_area)

class AppsCard(Gtk.Box):
    def __init__(self, apps_data):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.add_css_class("card")
        self.set_hexpand(True)

        title = Gtk.Label(label="Most Used", xalign=0)
        title.add_css_class("card-title-lg")
        self.append(title)

        # Take top 3 apps
        top_apps = apps_data[:3]
        max_duration = top_apps[0][1] if top_apps else 1

        colors = ["progress-fill-primary", "progress-fill-safari", "progress-fill-tertiary"]
        bg_colors = ["#000000", "#0070eb", "#4A154B"]

        for i, (app_name, duration) in enumerate(top_apps):
            app_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

            info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

            # Mock Icon
            icon_area = Gtk.DrawingArea()
            icon_area.set_size_request(32, 32)
            # Use default args hack to bind loop variable properly
            def draw_icon(area, cr, width, height, color=bg_colors[i%len(bg_colors)]):
                cr.set_source_rgba(*[int(color[j:j+2], 16)/255 for j in (1,3,5)], 1.0)
                cr.rectangle(0, 0, width, height)
                cr.fill()
            icon_area.set_draw_func(draw_icon)

            name_lbl = Gtk.Label(label=app_name)
            name_lbl.add_css_class("app-name")
            name_lbl.set_margin_start(12)

            h = int(duration // 3600)
            m = int((duration % 3600) // 60)
            time_str = f"{h}h {m}m" if h > 0 else f"{m}m"

            time_lbl = Gtk.Label(label=time_str, xalign=1)
            time_lbl.add_css_class("app-duration")
            time_lbl.set_hexpand(True)

            info_box.append(icon_area)
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
            self.append(app_box)

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
