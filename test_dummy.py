import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

app = Gtk.Application()
print("GTK4 can be imported!")
