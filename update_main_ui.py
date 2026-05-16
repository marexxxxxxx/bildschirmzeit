import sys

with open("main_ui.py", "r") as f:
    content = f.read()

# Make Productivity Tracker scrollable
old_prod_tracker_init = """        # View 2: Productivity Tracker (Categories)
        self.prod_tracker_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_stack.add_named(self.prod_tracker_box, "prod_tracker")"""

new_prod_tracker_init = """        # View 2: Productivity Tracker (Categories)
        self.prod_scrolled = Gtk.ScrolledWindow()
        self.prod_scrolled.set_vexpand(True)
        self.prod_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.prod_tracker_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.prod_scrolled.set_child(self.prod_tracker_box)

        self.main_stack.add_named(self.prod_scrolled, "prod_tracker")"""

content = content.replace(old_prod_tracker_init, new_prod_tracker_init)

with open("main_ui.py", "w") as f:
    f.write(content)
