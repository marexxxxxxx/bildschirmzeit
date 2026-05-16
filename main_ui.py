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
        self.prod_scrolled = Gtk.ScrolledWindow()
        self.prod_scrolled.set_vexpand(True)
        self.prod_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.prod_tracker_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.prod_scrolled.set_child(self.prod_tracker_box)

        self.main_stack.add_named(self.prod_scrolled, "prod_tracker")

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

        # Handle Standard Header visibility
        if hasattr(self, 'standard_header'):
            if view_name == "create_category":
                self.standard_header.set_visible(False)
            else:
                self.standard_header.set_visible(True)

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

        # Custom Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.add_css_class("header")
        header_box.set_margin_bottom(0)

        left_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        left_header.set_valign(Gtk.Align.CENTER)

        back_btn = Gtk.Button()
        back_btn.set_icon_name("go-previous-symbolic")
        back_btn.add_css_class("icon-button")
        back_btn.connect("clicked", lambda x: self.switch_to_view("prod_tracker", "Productivity Tracker"))

        title_lbl = Gtk.Label(label="Create Category")
        title_lbl.add_css_class("header-title")

        left_header.append(back_btn)
        left_header.append(title_lbl)

        right_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        right_header.set_halign(Gtk.Align.END)
        right_header.set_hexpand(True)
        right_header.set_valign(Gtk.Align.CENTER)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("secondary-button")
        cancel_btn.connect("clicked", lambda x: self.switch_to_view("prod_tracker", "Productivity Tracker"))

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("primary-button")

        def on_save(btn):
            name = getattr(self, "name_entry", Gtk.Entry()).get_text().strip()
            if not name:
                return
            # Use fixed value for is_prod since it's removed from UI
            is_prod = True
            cat_id = dashboard_data.add_category(name, self.selected_color, is_prod)
            if cat_id is not None and self.selected_apps:
                dashboard_data.assign_apps_to_category(cat_id, list(self.selected_apps))

            self.switch_to_view("prod_tracker", "Productivity Tracker")

        save_btn.connect("clicked", on_save)

        right_header.append(cancel_btn)
        right_header.append(save_btn)

        header_box.append(left_header)
        header_box.append(right_header)

        self.create_category_box.append(header_box)

        # Content Scrolled Window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        self.create_category_box.append(scrolled)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_top(48)
        content_box.set_margin_bottom(48)
        content_box.set_margin_start(40)
        content_box.set_margin_end(40)
        content_box.set_spacing(32)
        scrolled.set_child(content_box)

        # State
        self.selected_color = "#E57373"
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

        # Color Label
        color_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        color_label = Gtk.Label(label="Color Label")
        color_label.add_css_class("label-md")
        color_label.set_halign(Gtk.Align.START)

        colors = ["#E57373", "#81C784", "#64B5F6", "#BA68C8", "#FFB74D"]
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        color_box.add_css_class("input-field") # Make it look like a container
        color_box.set_valign(Gtk.Align.CENTER)
        color_box.set_margin_top(0) # reset margin

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
                cr.arc(width/2, height/2, min(width, height)/2 - 2, 0, 2*3.14159)
                cr.set_source_rgb(r, g, b)
                cr.fill()

                # Draw checkmark if selected
                if hex_c == self.selected_color:
                    cr.set_source_rgb(1, 1, 1) # white
                    cr.set_line_width(2)
                    cr.move_to(width*0.3, height*0.5)
                    cr.line_to(width*0.45, height*0.65)
                    cr.line_to(width*0.7, height*0.35)
                    cr.stroke()

            da = Gtk.DrawingArea()
            da.set_size_request(24, 24)
            da.set_draw_func(draw_color_btn)
            btn.set_child(da)

            def on_color_click(b, hex_c=c):
                self.selected_color = hex_c
                for c_btn in self.color_buttons.values():
                    c_btn.remove_css_class("selected")
                    # force redraw to update checkmark
                    child = c_btn.get_child()
                    if child:
                        child.queue_draw()
                b.add_css_class("selected")

            btn.connect("clicked", on_color_click)
            self.color_buttons[c] = btn
            color_box.append(btn)

        color_vbox.append(color_label)
        color_vbox.append(color_box)

        input_grid.append(name_vbox)
        input_grid.append(color_vbox)
        details_card.append(input_grid)
        content_box.append(details_card)

        # Assign Apps Section
        apps_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        apps_card.add_css_class("card")
        apps_card.set_vexpand(True)

        apps_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        apps_title = Gtk.Label(label="Assign Apps")
        apps_title.add_css_class("headline-md")
        apps_title.set_halign(Gtk.Align.START)
        apps_header.append(apps_title)

        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Search applications...")
        search_entry.set_halign(Gtk.Align.END)
        search_entry.set_hexpand(True)
        search_entry.add_css_class("input-field")
        apps_header.append(search_entry)

        apps_card.append(apps_header)

        recent_lbl = Gtk.Label(label="RECENTLY OPENED")
        recent_lbl.add_css_class("label-sm")
        recent_lbl.set_halign(Gtk.Align.START)
        apps_card.append(recent_lbl)

        apps_flow = Gtk.FlowBox()
        apps_flow.set_max_children_per_line(2)
        apps_flow.set_min_children_per_line(1)
        apps_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        apps_flow.set_row_spacing(16)
        apps_flow.set_column_spacing(16)
        apps_flow.set_homogeneous(True)

        tracked_apps = dashboard_data.get_all_tracked_apps()

        for app in tracked_apps:
            # We use a button to act as the assign item
            item_btn = Gtk.Button()
            item_btn.add_css_class("app-assign-item")

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)

            # Use create_app_icon if we want actual icons, or generic for now
            # To simplify and avoid circular import issues we use generic logic
            icon_da = Gtk.DrawingArea()
            icon_da.set_size_request(32, 32)
            def draw_icon_bg(area, cr, width, height, app_n=app):
                # draw a simple colored rounded rect
                cr.set_source_rgb(0.9, 0.9, 0.95)
                cr.arc(8, 8, 8, math.pi, 1.5*math.pi)
                cr.arc(width-8, 8, 8, 1.5*math.pi, 2*math.pi)
                cr.arc(width-8, height-8, 8, 0, 0.5*math.pi)
                cr.arc(8, height-8, 8, 0.5*math.pi, math.pi)
                cr.fill()
            icon_da.set_draw_func(draw_icon_bg)

            # Icon overlay
            icon_overlay = Gtk.Overlay()
            icon_overlay.set_child(icon_da)
            actual_icon = Gtk.Image(icon_name="application-x-executable")
            actual_icon.set_valign(Gtk.Align.CENTER)
            actual_icon.set_halign(Gtk.Align.CENTER)
            icon_overlay.add_overlay(actual_icon)

            text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            name_lbl = Gtk.Label(label=app)
            name_lbl.add_css_class("label-md")
            name_lbl.add_css_class("text-on-surface")
            name_lbl.set_halign(Gtk.Align.START)

            sub_lbl = Gtk.Label(label="Application") # mock sublabel
            sub_lbl.add_css_class("label-md")
            sub_lbl.set_halign(Gtk.Align.START)

            text_vbox.append(name_lbl)
            text_vbox.append(sub_lbl)
            text_vbox.set_hexpand(True)
            text_vbox.set_valign(Gtk.Align.CENTER)

            # Custom Toggle Button UI
            toggle_box = Gtk.Box()
            toggle_box.add_css_class("app-toggle-btn")
            toggle_box.set_size_request(24, 24)
            toggle_box.set_valign(Gtk.Align.CENTER)

            toggle_icon = Gtk.Image(icon_name="list-add-symbolic")
            toggle_icon.set_valign(Gtk.Align.CENTER)
            toggle_icon.set_halign(Gtk.Align.CENTER)
            toggle_box.append(toggle_icon)

            box.append(icon_overlay)
            box.append(text_vbox)
            box.append(toggle_box)

            item_btn.set_child(box)

            def toggle_app(btn, t_box=toggle_box, t_icon=toggle_icon, a=app):
                is_selected = a in self.selected_apps
                if is_selected:
                    btn.remove_css_class("selected")
                    t_box.remove_css_class("active")
                    t_icon.set_from_icon_name("list-add-symbolic")
                    self.selected_apps.discard(a)
                else:
                    btn.add_css_class("selected")
                    t_box.add_css_class("active")
                    t_icon.set_from_icon_name("object-select-symbolic")
                    self.selected_apps.add(a)

            item_btn.connect("clicked", toggle_app)

            apps_flow.append(item_btn)

        apps_card.append(apps_flow)
        content_box.append(apps_card)


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
        self.standard_header = header

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
