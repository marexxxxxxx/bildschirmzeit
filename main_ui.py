import sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import dashboard_data
from cards import SummaryCard, ChartCard, AppsCard, CategoriesCard

class ScreenTimeWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Screen Time Dashboard")
        self.set_default_size(1200, 800)

        self.load_css()

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(main_box)

        sidebar = self.create_sidebar()
        main_box.append(sidebar)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_hexpand(True)
        main_box.append(content_box)

        header = self.create_header()
        content_box.append(header)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_box.append(scrolled_window)

        # Main Grid Area
        self.grid_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.grid_box.set_margin_top(48)
        self.grid_box.set_margin_bottom(48)
        self.grid_box.set_margin_start(40)
        self.grid_box.set_margin_end(40)

        self.build_dashboard()

        scrolled_window.set_child(self.grid_box)

        # Set up a timer to refresh the dashboard every 60 seconds
        GLib.timeout_add_seconds(60, self.refresh_dashboard)

    def refresh_dashboard(self):
        # Remove existing children
        while child := self.grid_box.get_first_child():
            self.grid_box.remove(child)

        # Rebuild dashboard
        self.build_dashboard()
        return True

    def load_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('style.css')
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def build_dashboard(self):
        # Fetch Data
        total_time = dashboard_data.get_total_screen_time()
        weekly_data = dashboard_data.get_weekly_usage_by_day_and_category()
        apps_data = dashboard_data.get_most_used_apps()
        categories_data = dashboard_data.get_categories()

        # Top Row (Summary + Chart)
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        top_row.set_homogeneous(False)

        summary = SummaryCard(total_time)
        summary.set_size_request(300, -1)

        chart = ChartCard(weekly_data)

        top_row.append(summary)
        top_row.append(chart)
        self.grid_box.append(top_row)

        # Bottom Row (Apps + Categories)
        bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        bottom_row.set_homogeneous(True)

        apps = AppsCard(apps_data)
        categories = CategoriesCard(categories_data)

        bottom_row.append(apps)
        bottom_row.append(categories)
        self.grid_box.append(bottom_row)

    def create_sidebar(self):
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        sidebar.add_css_class("sidebar")
        sidebar.set_size_request(280, -1)
        sidebar.set_margin_top(32)
        sidebar.set_margin_bottom(32)
        sidebar.set_margin_start(16)
        sidebar.set_margin_end(16)

        profile_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        avatar = Gtk.DrawingArea()
        avatar.set_size_request(40, 40)
        def draw_avatar(area, cr, width, height):
            cr.arc(width/2, height/2, min(width, height)/2, 0, 2*3.14159)
            cr.set_source_rgb(0.8, 0.8, 0.8)
            cr.fill()
        avatar.set_draw_func(draw_avatar)
        profile_box.append(avatar)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title = Gtk.Label(label="Screen Time", xalign=0)
        title.add_css_class("sidebar-title")
        subtitle = Gtk.Label(label="Last synced: 2m ago", xalign=0)
        subtitle.add_css_class("sidebar-subtitle")
        vbox.append(title)
        vbox.append(subtitle)
        profile_box.append(vbox)
        sidebar.append(profile_box)

        tabs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        tabs_box.set_vexpand(True)

        overview = Gtk.Label(label="Overview", xalign=0)
        overview.add_css_class("sidebar-item")
        overview.add_css_class("active")

        blocked = Gtk.Label(label="Blocked Apps", xalign=0)
        blocked.add_css_class("sidebar-item")

        prod = Gtk.Label(label="Productivity Tracker", xalign=0)
        prod.add_css_class("sidebar-item")

        tabs_box.append(overview)
        tabs_box.append(blocked)
        tabs_box.append(prod)
        sidebar.append(tabs_box)

        footer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        settings = Gtk.Label(label="Settings", xalign=0)
        settings.add_css_class("sidebar-item")
        help = Gtk.Label(label="Help", xalign=0)
        help.add_css_class("sidebar-item")
        footer_box.append(settings)
        footer_box.append(help)
        sidebar.append(footer_box)

        return sidebar

    def create_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.add_css_class("header")

        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        title = Gtk.Label(label="Overview")
        title.add_css_class("header-title")
        date_badge = Gtk.Label(label="Today, Oct 24")
        date_badge.add_css_class("header-date")
        date_badge.set_valign(Gtk.Align.CENTER)

        left_box.append(title)
        left_box.append(date_badge)

        right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        right_box.set_halign(Gtk.Align.END)
        right_box.set_hexpand(True)

        share_btn = Gtk.Button(label="Share")
        share_btn.add_css_class("share-button")
        share_btn.set_valign(Gtk.Align.CENTER)

        limit_btn = Gtk.Button(label="Add Limit")
        limit_btn.add_css_class("add-limit-button")
        limit_btn.set_valign(Gtk.Align.CENTER)

        right_box.append(share_btn)
        right_box.append(limit_btn)

        header.append(left_box)
        header.append(right_box)
        return header

class ScreenTimeApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.example.ScreenTime")

    def do_activate(self):
        win = ScreenTimeWindow(application=self)
        win.present()

if __name__ == '__main__':
    app = ScreenTimeApp()
    sys.exit(app.run(sys.argv))
