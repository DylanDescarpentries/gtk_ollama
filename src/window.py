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

from typing import List, Optional, Dict, Union

import json
from gi.repository import Adw, Gtk, Gdk, Gio
from .ollama_client import Ollama_client
from .ollama_model import Ollama_model


@Gtk.Template(resource_path="/org/descarpentries/gtk_ollama/window.ui")
class GtkOllamaWindow(Adw.ApplicationWindow):
    __gtype_name__ = "OllamaGtkWindow"

    # Déclarations des enfants de l'interface
    combo_models_list: Gtk.ComboBoxText = Gtk.Template.Child()
    user_entry: Gtk.TextView = Gtk.Template.Child()
    messages_list: Gtk.ListBox = Gtk.Template.Child()
    conversations_list: Gtk.ListBox = Gtk.Template.Child()
    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    conv_title: Gtk.Label = Gtk.Template.Child()
    edit_title_button: Gtk.Button = Gtk.Template.Child()
    edit_title_label:Gtk.EditableLabel = Gtk.Template.Child()


    # Déclarations des variables transversales
    toggle_buttons: List[Gtk.ToggleButton] = []
    active_toggle_button: Optional[Gtk.ToggleButton] = None

    ollama_model: Ollama_model
    ollama_client: Ollama_client

    def __init__(self, **kwargs: Dict[str, Union[str, int, float]]) -> None:
        super().__init__(**kwargs)
        self.apply_styles()

        # Initialisation des modèles et clients
        self.ollama_model = Ollama_model()
        self.ollama_model.load_from_file()
        self.ollama_client = Ollama_client()

        self.add_default_models_to_combo_models_list()
        self.load_conversations_to_panel()


    def apply_styles(self) -> None:
        """Applique les styles CSS à l'interface."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource("/org/descarpentries/gtk_ollama/styles/styles.css")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def get_model_active(self) -> Optional[str]:
        """Récupère le modèle actuellement actif dans le combo box."""
        return self.combo_models_list.get_active_text()

    def get_user_input(self) -> str:
        """Récupère la saisie de l'utilisateur et efface le champ."""
        buffer = self.user_entry.get_buffer()
        user_input = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True).strip()
        buffer.set_text("")  # Efface le champ
        return user_input

    @Gtk.Template.Callback()
    def on_send_button_clicked(self, button: Gtk.Button) -> None:
        """
        Callback exécuté lorsque le bouton d'envoi est cliqué.
        Envoie une requête au client LLM en utilisant le modèle de gestion des conversations.
        """
        model = self.get_model_active()
        if not model:
            self.toast_overlay.add_toast(Adw.Toast(title="Aucun modèle actif"))
            return

        user_input = self.get_user_input()
        if not user_input:
            self.toast_overlay.add_toast(Adw.Toast(title="Saisie utilisateur vide"))
            return

        self.add_message_to_list(user_input)
        self.ask_response(model, user_input)

    @Gtk.Template.Callback()
    def on_trash_button_clicked(self, button: Gtk.Button) -> None:
        """
        Callback ecécuté lorsque le bouton de suppresion est cliqué.
        Supprime la conversation active
        """
        print("suppression en cours...")
        conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None
        self.ollama_model.delete_conversation(conv_id)
        self.clear_messages_list()
        self.load_conversations_to_panel()

    @Gtk.Template.Callback()
    def on_edit_title_button_clicked(self, button: Gtk.Button) -> None:
        if not self.active_toggle_button:
            return
        # Affiche le champ d'édition
        self.edit_title_button.set_visible(False)
        self.edit_title_label.set_visible(True)
        # Force le démarrage de l'édition
        self.edit_title_label.start_editing()

    @Gtk.Template.Callback()
    def on_title_text_change(self, editableLabel: Gtk.EditableLabel) -> None:
        conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None
        title = self.edit_title_label.get_text()
        conversation = self.ollama_model.get_conversation(conv_id)
        conversation['title'] = title
        self.load_conversations_to_panel()

    @Gtk.Template.Callback()
    def on_title_edit_change(self, editableLabel: Gtk.EditableLabel, param) -> None:
        # Vérifie si l'édition a été terminée
        if not self.edit_title_label.get_editing():
            print("Fin de l'édition détectée")

            # Récupère et traite les données
            conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None
            print(f"ID de conversation actif: {conv_id}")

            title = self.edit_title_label.get_text()
            print(f"Titre saisi: {title}")

            conversation = self.ollama_model.get_conversation(conv_id)
            if conversation:
                conversation['title'] = title
                print(f"Conversation mise à jour: {conversation}")
                self.load_conversations_to_panel()
                self.ollama_model.save_to_file()

            # Réinitialise l'interface utilisateur
            self.edit_title_button.set_visible(True)
            self.edit_title_label.set_visible(False)
            print("Mise à jour de l'interface terminée")

    def ask_response(self, model: str, user_input: str) -> None:
        """Envoie une requête au client et met à jour l'interface."""
        conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None
        print(conv_id)

        if conv_id is None:  # Pas de conversation active
            title = self.ollama_client.create_default_title({"user": user_input})
            self.toast_overlay.add_toast(Adw.Toast(title="Nouvelle conversation"))

            # Crée une nouvelle conversation
            new_conv_id = self.ollama_model.add_conversation(model, title, user_input, "")
            self.add_conversation_to_panel(title)  # Ajoute à l'interface
            self.ollama_model.save_to_file()
            self.load_conversations_to_panel()

            # Charger cette nouvelle conversation comme active
            self.active_toggle_button = new_conv_id
            active_conversation = self.ollama_model.set_active_conversation(new_conv_id)
        else:  # Une conversation active existe
            active_conversation = self.ollama_model.set_active_conversation(conv_id)
        # Récupérer l'historique des conversations
        history_conv = self.ollama_model.conversations

        # Obtenir une réponse à partir du modèle
        response = self.ollama_client.response(model=model, history_conv=history_conv, user_input=user_input)
        self.add_message_to_list(response)

        # Mise à jour de la conversation active
        if active_conversation:
            self.ollama_model.update_conversation(
                conv_id=active_conversation["id"],
                user_input=user_input,
                assistant_response=response,
            )

        # Sauvegarder les modifications
        self.ollama_model.save_to_file()

    def add_message_to_list(self, text: str) -> None:
        """Ajoute un message à la liste des messages."""
        label = Gtk.Label(label=text, halign=Gtk.Align.START, wrap=True)
        row = Gtk.ListBoxRow()
        row.set_child(label)
        self.messages_list.append(row)

    def clear_messages_list(self) -> None:
        """Efface tous les messages de la liste."""
        self.messages_list.remove_all()

    def load_conversations_to_panel(self) -> None:
        """Ajoute les conversations à la liste sous forme de boutons."""
        if self.conversations_list:
            self.toggle_buttons.clear()
            self.conversations_list.remove_all()
            for conversation in self.ollama_model.get_all_conversations():
                button = Gtk.ToggleButton(label=conversation["title"])
                button.conversation_id = conversation["id"]  # type: ignore
                button.connect("toggled", self.on_conversation_selected)
                self.toggle_buttons.append(button)

                row = Gtk.ListBoxRow()
                row.set_child(button)
                self.conversations_list.set_selection_mode(Gtk.SelectionMode.NONE)
                self.conversations_list.append(row)

    def add_conversation_to_panel(self, title: str) -> None:
        button = Gtk.ToggleButton(label=title)
        button.conversation_id = len(self.ollama_model.get_all_conversations()) + 1
        button.connect("toggled", self.on_conversation_selected)
        self.toggle_buttons.append(button)

    def on_conversation_selected(self, button: Gtk.ToggleButton) -> None:
        """Gère la sélection d'une conversation."""
        if button.get_active():
            self.active_toggle_button = button
            for other_button in self.toggle_buttons:
                if other_button != button:
                    other_button.set_active(False)

            conv_id = button.conversation_id
            print("conversation selectionné : ",conv_id)
            conversation = self.ollama_model.get_conversation(conv_id)
            self.load_conversation_to_chat(conversation)
            self.load_active_model(conversation)
            title = conversation['title']
            self.conv_title.set_label(title)

    def load_active_model(self, conversation: Dict[str, str]) -> None:
        """Active le modèle dans le GtkComboBoxText."""
        model = conversation["model"]
        for index, item in enumerate(self.combo_models_list.get_model()):
            self.combo_models_list.set_active(index)
            if self.combo_models_list.get_active_text() == model:
                return

        self.combo_models_list.set_active(-1)

    def load_conversation_to_chat(self, conversation: Dict[str, Union[str, List[Dict[str, str]]]]) -> None:
        """Charge les messages d'une conversation dans l'interface."""
        self.clear_messages_list()
        for message in conversation["history"]:
            self.add_message_to_list(message["content"])

    def add_default_models_to_combo_models_list(self) -> None:
        """Remplit le GtkComboBoxText avec les noms des modèles."""
        try:
            names_model = self.ollama_client.get_name_model()
            if not names_model:
                self.combo_models_list.append_text("Aucun modèle disponible")
                return

            for name in names_model:
                self.combo_models_list.append_text(name)
                self.combo_models_list.set_active(0)
        except Exception as e:
            if not self.combo_models_list:
                print("mdr")
            else:
                self.combo_models_list.append_text("Erreur lors du chargement")

