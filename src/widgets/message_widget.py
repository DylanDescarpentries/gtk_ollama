import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

class Message_Widget(Gtk.Box):
    def __init__(self, text, user, delete_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(15)
        self.set_margin_end(15)

        # Définir l'alignement principal
        self.set_halign(Gtk.Align.END if user else Gtk.Align.START)

        # Conteneur principal pour les marges internes et le style
        main_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=5
        )
        self.append(main_container)

        # Appliquer les classes CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b"""
            .box_message {
                border-radius: 10px;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
                padding: 10px;
            }
            .message-user {
                background-color: #e0f7fa;
            }
            .message-received {
                background-color: #f1f8e9;
            }
            """
        )
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        main_container.add_css_class("box_message")
        main_container.add_css_class("message-user" if user else "message-received")

        # Header : Boutons (modifier, supprimer)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header.set_halign(Gtk.Align.END)
        modify_button = Gtk.Button(label="Editer")
        delete_button = Gtk.Button(label="Supprimer")
        delete_button.set_icon_name("user-trash-symbolic")
        delete_button.connect("clicked", lambda btn: delete_callback(self))
        header.append(modify_button)
        header.append(delete_button)
        main_container.append(header)

        # Corps : Texte du message
        message_label = Gtk.Label(
            label=text,
            wrap=True,
            halign=Gtk.Align.START if user else Gtk.Align.END
        )
        message_label.set_margin_top(5)
        message_label.set_margin_bottom(5)
        main_container.append(message_label)


    def on_delete_clicked(self, button):
        """Callback pour le bouton supprimer."""
        if self.on_delete_callback:
            self.on_delete_callback(self)

