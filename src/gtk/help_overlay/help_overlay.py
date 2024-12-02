from gi.repository import Gtk, Gio, Adw


@Gtk.Template(resource_path="/org/descarpentries/gtk_ollama/gtk/help_overlay/help-overlay.ui")
class Help_Overlay_ShortcutsWindow(Gtk.ShortcutsWindow):
    __gtype_name__ = "HelpOverlayShortcutsWindow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
