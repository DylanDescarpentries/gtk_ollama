from gi.repository import Gtk, Gio

@Gtk.Template(resource_path="/org/descarpentries/gtk_ollama/gtk/manage_model/manage_model.ui")
class Manage_Model_Window(Gtk.Window):
    __gtype_name__ = "Manage_Model_Window"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

