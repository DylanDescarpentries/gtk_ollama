# main.py
#
# Copyright 2024 Dylan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys # type: ignore
import gi, os, subprocess, threading

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import GtkOllamaWindow # type: ignore
from pathlib import Path
from .help_overlay import Help_Overlay_ShortcutsWindow # type: ignore
from .ollama_model import Ollama_model # type: ignore
from .ollama_get_models import scrape_ollama_library # type: ignore

from gradio_client import Client


class GtkOllamaApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='org.descarpentries.gtk_ollama',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.create_action('help', self.on_help_action, ['F1'])
        self.create_action('open_save', self.on_open_save, ['<primary>o'])
        self.create_action('new_conv', self.on_new_conv, ['<primary>n'])
        self.create_action('change_view', self.on_view_change)
        self.create_action('actualize_model', self.on_actualize_model)
        self.create_action('closed_window', self.on_close_window)
        
        # methode exporter par dbus
        self.lookup_action("closed_window").set_enabled(True)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = GtkOllamaWindow(application=self)
        win.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_close_window(self, *args):
        win = self.props.active_window
        if win:
            win.hide()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='gtk_ollama',
                                application_icon='org.descarpentries.gtk_ollama',
                                developer_name='Dylan',
                                version='0.1.0',
                                developers=['Dylan'],
                                copyright='© 2024 Dylan')

        about.set_translator_credits(_('translator-credits')) # type: ignore
        about.present(self.props.active_window)

    def on_help_action(self, *args):
        """Callback for the app.help action"""
        # Crée une instance de la fenêtre si elle n'existe pas déjà
        helpwin = getattr(self, "_help_overlay_window", None)
        if not helpwin:
            helpwin = Help_Overlay_ShortcutsWindow()
            self._help_overlay_window = helpwin
        helpwin.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print('app.preferences action activated')

    def on_open_save(self, *args):
        # Récupérer la fenêtre active comme parent
        parent_window = self.props.active_window

        # Vérifier qu'il y a une fenêtre active
        if not parent_window:
            print("Erreur : aucune fenêtre active pour afficher la boîte de dialogue.")
            return

        # Création de la boîte de dialogue
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner un fichier",
            transient_for=parent_window,  # Utiliser la fenêtre active comme parent
            modal=True,  # Modale pour bloquer la fenêtre principale
        )
        dialog.set_action(Gtk.FileChooserAction.OPEN)  # Action : ouvrir un fichier

        # Ajout des boutons pour la boîte de dialogue
        dialog.add_buttons(
            "_Annuler", Gtk.ResponseType.CANCEL,
            "_Ouvrir", Gtk.ResponseType.OK
        )

        # Connecter un signal pour gérer la réponse utilisateur
        dialog.connect("response", self.on_file_chooser_response)

        # Afficher la boîte de dialogue
        dialog.show()

    def on_file_chooser_response(self, dialog, response):
        """Callback pour gérer la réponse de la boîte de dialogue."""
        if response == Gtk.ResponseType.OK:
            print("Fichier sélectionné :", dialog.get_file().get_path())
        elif response == Gtk.ResponseType.CANCEL:
            print("Action annulée.")

        # Fermer et détruire la boîte de dialogue
        dialog.close()

    def on_new_conv(self, *args):
        self.props.active_window.active_toggle_button =  None
        self.props.active_window._clear_messages()
        self.props.active_window.system_entry.get_buffer().set_text("")

        self.props.active_window.conv_title.set_text("Aucune conversation en cours")
        self.props.active_window.show_toast("Entrez un message pour débuter la nouvelle conversation")

    def on_view_change(self, *args):
        main_stack = self.props.active_window.main_view_container
        sidebar_stack = self.props.active_window.sidebar_container
        current_view = main_stack.get_visible_child()

        # Déterminer la prochaine vue à afficher
        if current_view == self.props.active_window.chat_container:
            main_stack.set_visible_child(self.props.active_window.manage_model_container)
            sidebar_stack.set_visible_child(self.props.active_window.model_available_container)

        else:
            main_stack.set_visible_child(self.props.active_window.chat_container)
            sidebar_stack.set_visible_child(self.props.active_window.conv_container)

    def on_actualize_model(self, *args):
        # Affiche le spinner / vue "searching"
        self.props.active_window.stack_model_buttons_options.set_visible_child(
            self.props.active_window.searching_available_models
        )

        def background_scrape():
            # Appelle le scraper dans le thread secondaire
            scrape_ollama_library()

            # Une fois terminé, met à jour l'UI dans le thread principal
            GLib.idle_add(finish_scrape_ui_update, self)

        def finish_scrape_ui_update(self_self):
            # Recharge les modèles et affiche le contenu final
            self_self.props.active_window._load_models_find()
            self_self.props.active_window.stack_model_buttons_options.set_visible_child(
                self_self.props.active_window.distant_buttons_options
            )
            return False  # Retourne False pour que GLib.idle_add ne rappelle pas la fonction

        # Lancement du thread
        threading.Thread(target=background_scrape, daemon=True).start()

def main(version):
    app = GtkOllamaApplication()
    return app.run(sys.argv)
