# window.py
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

import json
from gi.repository import Adw, Gtk, Gdk, Gio

from .ollama_client import Ollama_client
from .ollama_model import  Ollama_model


@Gtk.Template(resource_path='/org/descarpentries/gtk_ollama/window.ui')
class GtkOllamaWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'OllamaGtkWindow'
    # Déclarations des enfants de l'interface
    combo_models_list = Gtk.Template.Child()
    user_entry = Gtk.Template.Child()
    messages_list = Gtk.Template.Child()
    conversations_list = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apply_styles()
        # Initialisation de Ollama_client
        self.ollama_model = Ollama_model()
        self.ollama_model.load_from_file("/home/dylan/Documents/gtk_ollama/saves/saves.json")
        self.ollama_client = Ollama_client()
        self.add_default_models_to_combo_models_list()
        # Ajouter les modèles au GtkComboBoxText
        self.add_conversations_to_panel()

    def apply_styles(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource("/org/descarpentries/gtk_ollama/styles/styles.css")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def get_model_active(self):
        model = self.combo_models_list.get_active_text()
        if model:
            return model

    def get_user_input(self):
    # Récupérer le texte saisi par l'utilisateur
        user_input = self.user_entry.get_buffer().get_text(
            self.user_entry.get_buffer().get_start_iter(),
            self.user_entry.get_buffer().get_end_iter(),
            True
            )
        self.user_entry.get_buffer().set_text("")
        return user_input

    @Gtk.Template.Callback()
    def on_send_button_clicked(self, button):
        """
        Callback exécuté lorsque le bouton d'envoi est cliqué.
        Envoie une requête au client LLM en utilisant le modèle de gestion des conversations.
        """
        # Récupérer le modèle actif et la saisie utilisateur
        model = self.get_model_active()
        if not model:
            print("Aucun modèle actif.")
            self.toast_overlay.add_toast(Adw.Toast(title="Aucun modèle actif"))
            return

        user_input = self.get_user_input()
        if not user_input.strip():  # Ignore les entrées vides
            print("La saisie utilisateur est vide.")
            self.toast_overlay.add_toast(Adw.Toast(title="Saisie utilisateur vide"))
            return

        # Ajouter le message de l'utilisateur à l'interface
        self.add_message_to_list(user_input)

        # Récupérer l'historique des conversations pour ce modèle
        active_conversation = self.ollama_model.get_active_conversation()

        # Construire l'historique pour le modèle
        history_conv = self.ollama_model.conversations

        # Obtenir une réponse du modèle avec l'historique
        response = self.ollama_client.response(model=model, history_conv=history_conv, user_input=user_input)

        # Ajouter la réponse de l'assistant à l'interface
        self.add_message_to_list(response)

        # Mettre à jour ou ajouter la conversation
        if active_conversation:
            self.ollama_model.update_conversation(
                conv_id=active_conversation["id"],
                user_input=user_input,
                assistant_response=response,
            )
            print(f"Conversation mise à jour : {active_conversation}")
        else:
            self.ollama_model.add_conversation(model, user=user_input, assistant=response)
            print(f"Nouvelle conversation ajoutée : {self.ollama_model.list_conversations()}")
            # sauvegarde automatique la conversation en cours
        self.ollama_model.save_to_file()

    def add_message_to_list(self, text):
        """
        Ajoute un message à la liste des messages.
        """
        label = Gtk.Label(label=text, halign=Gtk.Align.START, wrap=True)  # Aligné à gauche
        row = Gtk.ListBoxRow()  # Crée une ligne
        row.set_child(label)  # Définit le label comme enfant de la ligne
        self.messages_list.append(row)  # Ajoute la ligne à la liste des messages

    def add_conversations_to_panel(self):
        """
        Ajoute les conversations à la liste de conversation sous forme de boutons avec les titres en label.
        """
        # Récupérer les titres des conversations
        titres = self.ollama_model.get_title()
        print("test caca prout ", titres)

        if not titres:
            print("Aucune conversation disponible pour l'ajout.")
            return

        # Ajouter chaque titre comme un bouton à la liste des conversations
        for titre in titres:
            # Créer un bouton avec le titre comme label
            button = Gtk.ToggleButton(label=titre)
            button.set_valign(Gtk.Align.START)  # Alignement vertical (optionnel)

            # Associer une action au bouton si nécessaire (facultatif)
            button.connect("toggled", self.on_conversation_selected, titre)

            # Créer une ligne pour le ListBox
            row = Gtk.ListBoxRow()
            row.set_child(button)

            # Ajouter la ligne à la liste des conversations
            self.conversations_list.append(row)

    def on_conversation_selected(self, button, titre):
        """
        Gère la sélection d'une conversation via le bouton correspondant.
        """
        if button.get_active():
            print(f"Conversation sélectionnée : {titre}")
        else:
            print(f"Conversation désélectionnée : {titre}")

    def add_default_models_to_combo_models_list(self):
        """
        Remplit le GtkComboBoxText avec les noms des modèles récupérés.
        """

        try:
            names_model = self.ollama_client.get_name_model()

            if not self.combo_models_list:
                print("combo_models_list n'a pas été initialisé correctement.")
                return
            if not names_model:
                print("Aucun modèle trouvé.")
                self.combo_models_list.append_text("Aucun modèle disponible")
                return

            # Ajouter les noms des modèles au combo box
            for name in names_model:
                self.combo_models_list.append_text(name)

        except Exception as e:
            print(f"Erreur lors du remplissage du GtkComboBoxText : {e}")
            self.combo_models_list.append_text("Erreur lors du chargement")

