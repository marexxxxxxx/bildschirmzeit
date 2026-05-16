import sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import dashboard_data
from cards import SummaryCard, ChartCard, AppsCard, CategoriesCard, ProductivityScoreCard, WorkVsLeisureCard, ProductivityCategoriesCard, RecentDeepWorkCard

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

        self.header_title_label = Gtk.Label(label="Overview")
        self.header_title_label.add_css_class("header-title")

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_hexpand(True)
        main_box.append(content_box)

        header = self.create_header()
        content_box.append(header)

        # Use a Stack to switch between different views
        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.main_stack.set_transition_duration(250)
        content_box.append(self.main_stack)

        # View 1: Overview
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.grid_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.grid_box.set_margin_top(48)
        self.grid_box.set_margin_bottom(48)
        self.grid_box.set_margin_start(40)
        self.grid_box.set_margin_end(40)

        self.build_dashboard()
        scrolled_window.set_child(self.grid_box)

        self.main_stack.add_named(scrolled_window, "overview")

        # View 2: Productivity Tracker (Categories)
        self.prod_tracker_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_stack.add_named(self.prod_tracker_box, "prod_tracker")

        # View 3: Create Category Form
        self.create_category_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_stack.add_named(self.create_category_box, "create_category")


        # Set up a timer to refresh the dashboard every 60 seconds
        GLib.timeout_add_seconds(60, self.refresh_dashboard)

    def switch_to_view(self, view_name, title_text):
        self.main_stack.set_visible_child_name(view_name)
        self.header_title_label.set_label(title_text)

        # Update active state in sidebar
        self.overview_label.remove_css_class("active")
        self.prod_label.remove_css_class("active")

        # Hide extra header buttons by default
        self.create_category_btn.set_visible(False)
        self.delete_category_btn.set_visible(False)
        self.header_tools_box.set_visible(False)

        if view_name == "overview":
            self.overview_label.add_css_class("active")
            self.refresh_dashboard()
        elif view_name == "prod_tracker":
            self.prod_label.add_css_class("active")
            self.create_category_btn.set_visible(True)
            self.delete_category_btn.set_visible(True)
            self.header_tools_box.set_visible(True)
            self.build_prod_tracker_view()
        elif view_name == "create_category":
            self.prod_label.add_css_class("active")
            self.build_create_category_view()

    def refresh_dashboard(self):
        if self.main_stack.get_visible_child_name() != "overview":
            return True
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

    def build_prod_tracker_view(self):
        # Clear existing children
        while child := self.prod_tracker_box.get_first_child():
            self.prod_tracker_box.remove(child)

        self.prod_tracker_box.set_margin_top(48)
        self.prod_tracker_box.set_margin_bottom(48)
        self.prod_tracker_box.set_margin_start(40)
        self.prod_tracker_box.set_margin_end(40)
        self.prod_tracker_box.set_spacing(24)

        # Build 2x2 Grid Layout

        # Top Row
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        top_row.set_homogeneous(False)

        score_card = ProductivityScoreCard(84, 5 * 3600 + 20 * 60) # 84%, 5h 20m focus time
        score_card.set_size_request(300, -1)

        chart_card = WorkVsLeisureCard(None)

        top_row.append(score_card)
        top_row.append(chart_card)

        self.prod_tracker_box.append(top_row)

        # Bottom Row
        bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        bottom_row.set_homogeneous(True)

        categories_data = [] # fetch categories mapping here if needed, passing empty uses mock
        cat_card = ProductivityCategoriesCard(categories_data)

        deep_work_card = RecentDeepWorkCard()

        bottom_row.append(cat_card)
        bottom_row.append(deep_work_card)

        self.prod_tracker_box.append(bottom_row)

    def build_create_category_view(self):
        # Clear existing children
        while child := self.create_category_box.get_first_child():
            self.create_category_box.remove(child)

        self.create_category_box.set_margin_top(48)
        self.create_category_box.set_margin_bottom(48)
        self.create_category_box.set_margin_start(40)
        self.create_category_box.set_margin_end(40)
        self.create_category_box.set_spacing(32)

        # State
        self.selected_color = "#E57373"
        self.is_productive = False
        self.selected_apps = set()

        # Category Details Section
        details_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        details_card.add_css_class("card")

        details_title = Gtk.Label(label="Category Details")
        details_title.add_css_class("headline-md")
        details_title.set_halign(Gtk.Align.START)
        details_card.append(details_title)

        input_grid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)

        # Name Input
        name_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        name_vbox.set_hexpand(True)
        name_label = Gtk.Label(label="Category Name")
        name_label.add_css_class("label-md")
        name_label.set_halign(Gtk.Align.START)

        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text("e.g. Design Work, Coding...")
        self.name_entry.add_css_class("input-field")

        name_vbox.append(name_label)
        name_vbox.append(self.name_entry)

        # Color & Productive
        options_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        options_label = Gtk.Label(label="Settings")
        options_label.add_css_class("label-md")
        options_label.set_halign(Gtk.Align.START)

        options_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)

        # Color Palette
        colors = ["#E57373", "#81C784", "#64B5F6", "#BA68C8", "#FFB74D"]
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self.color_buttons = {}
        for c in colors:
            btn = Gtk.Button()
            btn.add_css_class("color-btn")
            if c == self.selected_color:
                btn.add_css_class("selected")

            def draw_color_btn(area, cr, width, height, hex_c=c):
                r = int(hex_c[1:3], 16) / 255.0
                g = int(hex_c[3:5], 16) / 255.0
                b = int(hex_c[5:7], 16) / 255.0
                cr.arc(width/2, height/2, min(width, height)/2, 0, 2*3.14159)
                cr.set_source_rgb(r, g, b)
                cr.fill()

            da = Gtk.DrawingArea()
            da.set_size_request(32, 32)
            da.set_draw_func(draw_color_btn)
            btn.set_child(da)

            def on_color_click(b, hex_c=c):
                self.selected_color = hex_c
                for c_btn in self.color_buttons.values():
                    c_btn.remove_css_class("selected")
                b.add_css_class("selected")

            btn.connect("clicked", on_color_click)
            self.color_buttons[c] = btn
            color_box.append(btn)

        options_hbox.append(color_box)

        # Productive switch
        prod_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        prod_box.set_valign(Gtk.Align.CENTER)
        prod_lbl = Gtk.Label(label="Productive:")
        self.prod_switch = Gtk.Switch()
        self.prod_switch.set_valign(Gtk.Align.CENTER)
        prod_box.append(prod_lbl)
        prod_box.append(self.prod_switch)

        options_hbox.append(prod_box)

        options_vbox.append(options_label)
        options_vbox.append(options_hbox)

        input_grid.append(name_vbox)
        input_grid.append(options_vbox)
        details_card.append(input_grid)
        self.create_category_box.append(details_card)

        # Assign Apps Section
        apps_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        apps_card.add_css_class("card")
        apps_card.set_vexpand(True)

        apps_title = Gtk.Label(label="Assign Apps")
        apps_title.add_css_class("headline-md")
        apps_title.set_halign(Gtk.Align.START)
        apps_card.append(apps_title)

        recent_lbl = Gtk.Label(label="Recently Opened")
        recent_lbl.add_css_class("label-sm")
        recent_lbl.set_halign(Gtk.Align.START)
        apps_card.append(recent_lbl)

        apps_scrolled = Gtk.ScrolledWindow()
        apps_scrolled.set_vexpand(True)
        apps_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        apps_flow = Gtk.FlowBox()
        apps_flow.set_max_children_per_line(3)
        apps_flow.set_min_children_per_line(1)
        apps_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        apps_flow.set_row_spacing(16)
        apps_flow.set_column_spacing(16)

        tracked_apps = dashboard_data.get_all_tracked_apps()

        for app in tracked_apps:
            # We use a button to act as the assign item
            item_btn = Gtk.Button()
            item_btn.add_css_class("app-assign-item")

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)

            # icon stub
            icon = Gtk.Image(icon_name="application-x-executable")
            icon.set_pixel_size(32)

            name_lbl = Gtk.Label(label=app)
            name_lbl.add_css_class("label-md")
            name_lbl.add_css_class("text-on-surface")
            name_lbl.set_hexpand(True)
            name_lbl.set_halign(Gtk.Align.START)

            check = Gtk.CheckButton()
            check.set_valign(Gtk.Align.CENTER)

            box.append(icon)
            box.append(name_lbl)
            box.append(check)

            item_btn.set_child(box)

            def toggle_app(btn, chk, a=app):
                is_active = not chk.get_active()
                chk.set_active(is_active)
                if is_active:
                    btn.add_css_class("selected")
                    self.selected_apps.add(a)
                else:
                    btn.remove_css_class("selected")
                    self.selected_apps.discard(a)

            item_btn.connect("clicked", toggle_app, check)

            apps_flow.append(item_btn)

        apps_scrolled.set_child(apps_flow)
        apps_card.append(apps_scrolled)
        self.create_category_box.append(apps_card)

        # Save / Cancel Buttons at the bottom
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        btn_box.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("secondary-button")
        cancel_btn.connect("clicked", lambda x: self.switch_to_view("prod_tracker", "Productivity Tracker"))

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("primary-button")

        def on_save(btn):
            name = self.name_entry.get_text().strip()
            if not name:
                return
            is_prod = self.prod_switch.get_active()
            cat_id = dashboard_data.add_category(name, self.selected_color, is_prod)
            if cat_id is not None and self.selected_apps:
                dashboard_data.assign_apps_to_category(cat_id, list(self.selected_apps))

            self.switch_to_view("prod_tracker", "Productivity Tracker")

        save_btn.connect("clicked", on_save)

        btn_box.append(cancel_btn)
        btn_box.append(save_btn)

        self.create_category_box.append(btn_box)

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

        # Overview
        self.overview_label = Gtk.Label(label="Overview", xalign=0)
        self.overview_label.add_css_class("sidebar-item")
        self.overview_label.add_css_class("active")

        overview_event = Gtk.GestureClick()
        overview_event.connect("released", lambda gesture, n_press, x, y: self.switch_to_view("overview", "Overview"))
        self.overview_label.add_controller(overview_event)

        # Blocked Apps (stub)
        blocked = Gtk.Label(label="Blocked Apps", xalign=0)
        blocked.add_css_class("sidebar-item")

        # Productivity Tracker
        self.prod_label = Gtk.Label(label="Productivity Tracker", xalign=0)
        self.prod_label.add_css_class("sidebar-item")

        prod_event = Gtk.GestureClick()
        prod_event.connect("released", lambda gesture, n_press, x, y: self.switch_to_view("prod_tracker", "Productivity Tracker"))
        self.prod_label.add_controller(prod_event)

        tabs_box.append(self.overview_label)
        tabs_box.append(blocked)
        tabs_box.append(self.prod_label)
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
        date_badge = Gtk.Label(label="Today, Oct 24")
        date_badge.add_css_class("header-date")
        date_badge.set_valign(Gtk.Align.CENTER)

        left_box.append(self.header_title_label)
        left_box.append(date_badge)

        self.header_right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.header_right_box.set_halign(Gtk.Align.END)
        self.header_right_box.set_hexpand(True)

        # Standard header buttons
        self.share_btn = Gtk.Button(label="Share")
        self.share_btn.add_css_class("share-button")
        self.share_btn.set_valign(Gtk.Align.CENTER)

        self.limit_btn = Gtk.Button(label="Add Limit")
        self.limit_btn.add_css_class("add-limit-button")
        self.limit_btn.set_valign(Gtk.Align.CENTER)

        # Productivity tracker specific buttons
        self.create_category_btn = Gtk.Button(label="Create Category")
        self.create_category_btn.add_css_class("primary-button")
        self.create_category_btn.set_valign(Gtk.Align.CENTER)
        self.create_category_btn.connect("clicked", lambda x: self.switch_to_view("create_category", "Create Category"))
        self.create_category_btn.set_visible(False)

        self.delete_category_btn = Gtk.Button(label="Delete Category")
        self.delete_category_btn.add_css_class("secondary-button")
        self.delete_category_btn.add_css_class("outline-btn")
        self.delete_category_btn.set_valign(Gtk.Align.CENTER)
        self.delete_category_btn.set_visible(False)

        self.header_right_box.append(self.share_btn)
        self.header_right_box.append(self.create_category_btn)
        self.header_right_box.append(self.delete_category_btn)
        self.header_right_box.append(self.limit_btn)

        header.append(left_box)
        header.append(self.header_right_box)

        # Add a placeholder box for "header action tools" like calendar, filters as seen in screenshot
        self.header_tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.header_tools_box.set_valign(Gtk.Align.CENTER)

        cal_btn = Gtk.Button()
        cal_btn.set_icon_name("x-office-calendar-symbolic")
        cal_btn.add_css_class("icon-button")

        filter_btn = Gtk.Button()
        filter_btn.set_icon_name("view-filter-symbolic")
        filter_btn.add_css_class("icon-button")

        self.header_tools_box.append(cal_btn)
        self.header_tools_box.append(filter_btn)

        # Insert it before the main right box, but keep it hidden by default
        self.header_tools_box.set_visible(False)
        left_box.append(self.header_tools_box)

        return header

class ScreenTimeApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.example.ScreenTime")
        dashboard_data.init_categories_db()

    def do_activate(self):
        win = ScreenTimeWindow(application=self)
        win.present()

if __name__ == '__main__':
    app = ScreenTimeApp()
    sys.exit(app.run(sys.argv))
