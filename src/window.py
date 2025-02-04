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

import json, threading
from gi.repository import Adw, Gtk, Gdk, Gio, GLib
from .ollama_client import Ollama_client # type: ignore
from .ollama_model import Ollama_model # type: ignore
from .message_widget import Message_Widget # type: ignore

@Gtk.Template(resource_path="/org/descarpentries/gtk_ollama/window.ui")
class GtkOllamaWindow(Adw.ApplicationWindow):
    __gtype_name__ = "OllamaGtkWindow"

    # Déclarations des vues de l'interface'
    main_view_container = Gtk.Template.Child()
    manage_model_container = Gtk.Template.Child()
    chat_container = Gtk.Template.Child()
    sidebar_container = Gtk.Template.Child()
    conv_container = Gtk.Template.Child()
    model_available_container = Gtk.Template.Child()

    # Déclarations des enfants de l'interface principale
    scrolled_messages: Gtk.ScrolledWindow = Gtk.Template.Child()
    combo_models_list: Gtk.ComboBoxText = Gtk.Template.Child()
    user_entry: Gtk.TextView = Gtk.Template.Child()
    system_entry: Gtk.TextView = Gtk.Template.Child()
    messages_list: Gtk.ListBox = Gtk.Template.Child()
    conversations_list: Gtk.ListBox = Gtk.Template.Child()
    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    conv_title: Gtk.Label = Gtk.Template.Child()
    edit_title_button: Gtk.Button = Gtk.Template.Child()
    edit_title_label: Gtk.EditableLabel = Gtk.Template.Child()
    conv_options: Gtk.Box = Gtk.Template.Child()
    conv_option_set_visible: Gtk.Button = Gtk.Template.Child()
    temp_spin: Adw.SpinRow = Gtk.Template.Child()
    custom_option_modal: Gtk.Dialog = Gtk.Template.Child()
    sendSpinner: Adw.Spinner = Gtk.Template.Child()

    # Déclarations des enfants de l'interdace secondaire
    model_find:Gtk.ListBox = Gtk.Template.Child()
    model_infos:Adw.PreferencesGroup = Gtk.Template.Child()
    stack_model_buttons_options:Gtk.Stack = Gtk.Template.Child()
    local_buttons_options: Gtk.Box = Gtk.Template.Child()
    distant_buttons_options: Gtk.Box = Gtk.Template.Child()
    download_model_button: Gtk.Button = Gtk.Template.Child()
    

    # Déclarations des variables transversales
    toggle_buttons_conv: List[Gtk.ToggleButton] = []
    toggle_buttons_models: List[Gtk.ToggleButton] = []
    active_toggle_button: Optional[Gtk.ToggleButton] = None
    model_progress_bars: dict[str, Gtk.ProgressBar] = {}
    system_entry_await = ""

    def __init__(self, **kwargs: Dict[str, Union[str, int, float]]) -> None:
        super().__init__(**kwargs)
        display = Gdk.Display.get_default()
        if not display:
            print("Erreur : Impossible d'initialiser l'affichage GTK")
            return
        self.action_rows = []
        self.ollama_model = Ollama_model()
        self.ollama_client = Ollama_client()
        self.ollama_model.load_from_file()
        self.message_id_counter = 0
        self.downloading_models = None

        self.apply_styles()
        self._initialize_ui()

    def apply_styles(self) -> None:
        """Applique les styles CSS à l'interface."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource("/org/descarpentries/gtk_ollama/styles/styles.css")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _initialize_ui(self) -> None:
        """Initialize les éléments de l'interface"""
        self._populate_models_list()
        self._load_models_find()
        self._load_conversations()

    def _populate_models_list(self) -> None:
        """Remplit le GtkComboBoxText avec les noms des modèles."""
        for name in self.ollama_client.get_name_model():
            self.combo_models_list.append_text(name)

    def _get_user_input(self) -> str:
        """Récupère la saisie de l'utilisateur et efface le champ."""
        buffer = self.user_entry.get_buffer()
        user_input = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True).strip()
        buffer.set_text("")
        return user_input

    @Gtk.Template.Callback()
    def on_send_button_clicked(self, button: Gtk.Button) -> None:
        """Gestionnaire d'événements pour l'envoi d'un message."""
        model = self.combo_models_list.get_active_text()
        if not model:
            self._show_toast("Aucun modèle actif")
            return
        user_input = self._get_user_input()
        if not user_input:
            self._show_toast("Saisie utilisateur vide")
            return

        self._add_message(user_input, True)
        self.scroll_to_bottom()
        GLib.Thread.new("fetch_response", self._fetch_response, model, user_input)
        
    def scroll_to_bottom(self):
        """Fait défiler la ScrolledWindow vers le bas."""
        adj = self.scrolled_messages.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False  # Arrête l'idle_add une fois exécuté
    
    def delete_message(self, message_widget: Message_Widget) -> None:
        """Supprime un message de la conversation et met à jour l'interface et le fichier."""
        # Trouver le ListBoxRow correspondant à message_widget
        row_to_remove = None
        for row in self.messages_list:
            if row.get_child() == message_widget:
                row_to_remove = row
                break

        if row_to_remove:
            # Trouver l'ID de la conversation à partir du widget
            conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None

            # Supprimer le message du modèle de données (conversation)
            self.ollama_model.delete_message_from_conversation(conv_id, message_widget.get_message_id())  # Méthode à ajouter

            # Supprimer le row de la ListBox
            self.messages_list.remove(row_to_remove)

            # Sauvegarder la conversation dans le fichier
            self.ollama_model.save_to_file()

    def on_trash_dialog_confirm(self, dialog: Adw.MessageDialog, response: str) -> None:
        """Supprime la conversation active."""
        if response == "delete":
            conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None

            self.ollama_model.delete_conversation(conv_id)
            self._clear_messages()
            self.conv_title.set_label("Aucune conversation en cours")
            self.active_toggle_button = None
            self._load_conversations()

    def on_trash_model_dialog_confirm(self, dialog: Adw.MessageDialog, response: str) -> None:
        """Supprime le modele actif """
        model_name = self.active_toggle_button.model_data['name'] if self.active_toggle_button else "nom"
        self.ollama_client.delete_model(model_name)
        self.model_finds.remove_all()
        self._load_models_find()

    @Gtk.Template.Callback()
    def on_edit_title_button_clicked(self, button: Gtk.Button) -> None:
        """Affiche le champ d'édition pour le titre."""
        if self.active_toggle_button:
            self.edit_title_button.set_visible(False)
            self.edit_title_label.set_visible(True)
            self.edit_title_label.start_editing()

    @Gtk.Template.Callback()
    def on_title_text_change(self, editableLabel: Gtk.EditableLabel) -> None:
        conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None
        title = self.edit_title_label.get_text()
        conversation = self.ollama_model.get_conversation(conv_id)
        conversation['title'] = title
        self._load_conversations()

    @Gtk.Template.Callback()
    def on_title_edit_change(self, editableLabel: Gtk.EditableLabel, param) -> None:
        if not self.edit_title_label.get_editing():
            conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None
            title = self.edit_title_label.get_text()
            conversation = self.ollama_model.get_conversation(conv_id)
            if conversation:
                conversation['title'] = title
                self._load_conversations()
                self.ollama_model.save_to_file()

            self.edit_title_button.set_visible(True)
            self.edit_title_label.set_visible(False)

    def _update_conversation(self, conv_id: str, user_input: str, response: str) -> None:
        """Met à jour une conversation existante."""
        self._add_message(response, False)
        self.ollama_model.update_conversation(conv_id, user_input, response)
        self._load_conversations()
        self.ollama_model.save_to_file()

    def _create_new_conversation(self, model: str, user_input: str) -> None:
        """Crée une nouvelle conversation et met à jour l'interface."""
        title = self.ollama_client.create_default_title({"user": user_input})
        temp = self.temp_spin.get_value()
        self.sendSpinner.set_visible(True)

        # Initialiser une réponse complète
        full_response = self.stream_response(model=model, temp=temp, conversation={"system": self.system_entry_await}, user_input=user_input)

        self.sendSpinner.set_visible(False)

        # Ajouter la conversation au modèle avec la réponse complète
        new_conv = self.ollama_model.add_conversation(model, title, user_input, full_response)
        self._add_message(full_response, False)
        self._load_conversations()

        # Crée le bouton et l'assigne
        self.active_toggle_button = self._create_conversation_button(new_conv)
        # Active le bouton pour refléter correctement l'état
        self.active_toggle_button.set_active(True)
        self.ollama_model.save_to_file()

    def _fetch_response(self, model: str, user_input: str) -> None:
        """Récupère une réponse et met à jour l'interface en conséquence."""
        if self.active_toggle_button:
            self.sendSpinner.set_visible(True)
            conv_id = self.active_toggle_button.conversation_id
            temp = self.temp_spin.get_value()
            conversation = self.ollama_model.get_conversation(conv_id)

            # Consommer le stream de réponse
            full_response = self.stream_response(model=model, temp=temp, conversation=conversation, user_input=user_input)

            self.sendSpinner.set_visible(False)
            self._update_conversation(conv_id, user_input, full_response)
        else:
            new_conversation = self._create_new_conversation(model, user_input)

    def stream_response(self, model, temp, conversation, user_input) -> str:
        temp_message = Message_Widget("", user=False, delete_callback=self.delete_message, message_id=self.message_id_counter + 1)
        self.messages_list.append(temp_message)
        full_response = ""
        for chunk in self.ollama_client.response(model=model, temp=temp, conversation=conversation, user_input=user_input):
            safe_chunk = chunk.encode('utf-8', errors='replace').decode('utf-8')
            full_response += safe_chunk
            GLib.idle_add(temp_message.append_text, safe_chunk)
            self.scroll_to_bottom()
        temp_message.extract_docstring(full_response)
        return full_response

    def _update_conversation(self, conv_id: str, user_input: str, response: str) -> None:
        """Met à jour une conversation existante."""
        self.ollama_model.update_conversation(conv_id, user_input, response)
        self._load_conversations()
        self.ollama_model.save_to_file()

    def _add_message(self, text: str, user: bool) -> None:
        """Ajoute un message à la liste des messages."""
        message = Message_Widget(text, user, self.delete_message, self.message_id_counter +1)
        self.messages_list.append(message)

    def _clear_messages(self) -> None:
        """Efface tous les messages de la liste."""
        self.messages_list.remove_all()

    def _load_conversations(self) -> None:
        """Ajoute les conversations à la liste sous forme de boutons."""
        if self.conversations_list:
            self.toggle_buttons_conv.clear()
            self.conversations_list.remove_all()
            for conversation in self.ollama_model.get_all_conversations():
                button = Gtk.ToggleButton(label=conversation["title"])
                button.set_has_frame(False)
                button.set_hexpand(True)
                button.set_halign(Gtk.Align.FILL)  # Le bouton prend toute la largeur
                
                # Créer un conteneur pour aligner le texte à gauche
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                label = Gtk.Label(label=conversation["title"])
                label.set_halign(Gtk.Align.START)
                box.append(label)
                button.set_child(box)
                
                button.conversation_id = conversation["id"]
                button.connect("toggled", self.on_conversation_selected)
                self.toggle_buttons_conv.append(button)

                row = Gtk.ListBoxRow()
                row.set_child(button)
                self.conversations_list.set_selection_mode(Gtk.SelectionMode.NONE)
                self.conversations_list.append(row)

    def _load_models_find(self) -> None:
        """
        Charge les modèles locaux et distants depuis l'API et met à jour l'interface utilisateur.
        """
        if not self.model_find:
            self.show_toast("Erreur : la liste des modèles n'existe pas.")
            return
        local_models, distant_models = self.compare_model_lists_find()

        # Effacer les boutons précédents
        self.toggle_buttons_models.clear()
        self.model_find.remove_all()
        # Ajouter les modèles locaux
        if self.downloading_models:
            self.add_model_category(
                models=self.downloading_models,
                category_title="Modele en cours de Téléchargement...",
                toggle_button_callback=self.on_model_selected,
            )
        self.add_model_category(
            models=local_models,
            category_title="Modèles locaux",
            toggle_button_callback=self.on_model_selected,
        )
        self.add_model_category(
            models=distant_models,
            category_title="Modèles distant",
            toggle_button_callback=self.on_model_selected,
        )

    def move_model_category(self, model: list, category_title: str):
        if not self.downloading_models:
            self.downloading_models = []
            self.downloading_models.append(model)
            self._load_models_find()
        else:
            self.downloading_models.append(model)
            self._load_models_find()

    def compare_model_lists_find(self) -> list:
        """
        Compare la liste de modele distante à la local et supprime de
        la liste distante les model déjà installé en local
        """
        # Récupérer les modèles depuis les API
        local_models = self.ollama_client.get_list_models().get('models', [])
        distant_models = self.ollama_client.get_distant_models()
        # Supprimer les doublons entre local_models et distant_models
        local_model_names = {model['name'] for model in local_models}
        filtered_distant_models = [model for model in distant_models if model['name'] not in local_model_names]
        # Combiner les deux listes sans doublons
        models = local_models + filtered_distant_models

        return local_models, filtered_distant_models

    def add_model_category(self, models: list, category_title: str, toggle_button_callback) -> None:
        """
        Ajoute une catégorie de modèles avec un header et des boutons pour chaque modèle.

        :param models: Liste de modèles à afficher.
        :param category_title: Titre de la catégorie (ex: "Modèles locaux", "Modèles distants").
        :param toggle_button_callback: Callback à connecter aux boutons de chaque modèle.
        """
        if models:
            # Ajouter un header pour la catégorie
            header = Gtk.Label(label=category_title)
            header.get_style_context().add_class("list-group-header")
            header.set_halign(Gtk.Align.START)
            row_header = Gtk.ListBoxRow()
            row_header.set_activatable(False)
            row_header.set_child(header)
            self.model_find.append(row_header)

            # Ajouter les modèles de la catégorie
            for model_data in models:
                button = Gtk.ToggleButton(label=model_data['name'])
                button.set_has_frame(False)
                button.model_data = model_data
                button.connect("toggled", toggle_button_callback)
                button.set_halign(Gtk.Align.START)  # Aligne le bouton à droite
                self.toggle_buttons_models.append(button)

                # Créer une ligne pour chaque bouton de modèle
                row = Gtk.ListBoxRow()
                row.set_child(button)
                self.model_find.append(row)

    def _show_toast(self, message: str) -> None:
        """Affiche un toast avec un message donné."""
        self.toast_overlay.add_toast(Adw.Toast(title=message))

    @Gtk.Template.Callback()
    def on_personnalize_system_button_clicked(self, button: Gtk.Button):
        """
            Ouvre la modal de personnalisation du template system du model
        """
        conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None
        if conv_id:
            system = self.ollama_model.get_conversation(conv_id).get('system')
            if system:
                self.system_entry.get_buffer().set_text(str(system))

        # Associer le dialogue modal à cette fenêtre comme parent
        self.custom_option_modal.set_transient_for(self)
        # Rendre la boîte de dialogue visible
        GLib.idle_add(self.custom_option_modal.present)

    @Gtk.Template.Callback()
    def on_confirm_personnalize_system(self, button: Gtk.Button):
        """
        Enregistre la personnalisation du system dans la sauvegarde de la conversation
        """
        conv_id = self.active_toggle_button.conversation_id if self.active_toggle_button else None
        # Récupérer le texte de personnalisation
        buffer = self.system_entry.get_buffer()
        system_entry = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True).strip()

        if not conv_id:
            # Stocker le texte temporairement pour la prochaine conversation
            self.system_entry_await = system_entry
            self._show_toast("Personnalisation du système mise à jour.")
            return

        self.ollama_model.update_system_model(conv_id, system_entry)
        self.ollama_model.save_to_file()

    @Gtk.Template.Callback()
    def on_trash_button_clicked(self, button:Gtk.Button):
        """
        Supprime La conversation correspondant à l'id selectionné
        """
        if not self.active_toggle_button:
            self._show_toast("Aucune conversation active")
            return
        dialog = Adw.MessageDialog(
            transient_for=self,
            modal=True,
            body="Etes vous sur de vouloir supprimer cette conversation ?",
            close_response="cancel",
        )

        dialog.add_response("cancel", "_Cancel")
        dialog.add_response("delete", "Supprimer")

        dialog.set_response_appearance("delete", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self.on_trash_dialog_confirm)
        dialog.show()

    @Gtk.Template.Callback()
    def on_download_model_clicked(self, button: Gtk.Button):
        """
            Prépare les élément graphique du téléchargement
            et appel son téléchargement dans un Thread
        """
        # Récupérer le nom du modèle
        model_name = self.active_toggle_button.model_data['name'] if self.active_toggle_button else "nom"

        # Vérifier si une barre de progression existe déjà pour ce modèle
        if model_name not in self.model_progress_bars:
            # Créer une nouvelle barre de progression si nécessaire
            progress_bar = Gtk.ProgressBar()
            progress_bar.set_show_text(True)
            progress_bar.set_text("Téléchargement ...")
            progress_bar.set_fraction(0.0)

            # Ajouter la barre à un conteneur dans l'interface
            self.distant_buttons_options.append(progress_bar)
            self.model_progress_bars[model_name] = progress_bar

            #mettre à jour sa catégorie
            self.move_model_category(self.active_toggle_button.model_data, "model en cours de téléchargement...",)

        # Démarrer le téléchargement dans un thread séparé
        threading.Thread(target=self.downloading_model, args=(model_name,), daemon=True).start()

    def downloading_model(self, model_name: str):
        """
        Télécharge et met à jour la barre de progresssion
        """
        # Obtenir la barre de progression associée au modèle
        progress_bar = self.model_progress_bars.get(model_name)
        if not progress_bar:
            print(f"Aucune barre trouvée pour le modèle {model_name}")
            return

        # Réinitialiser la barre de progression
        GLib.idle_add(progress_bar.set_fraction, 0.0)

        # Appeler le générateur pour suivre la progression
        for progress in self.ollama_client.pull_model(model_name):
            if progress is None:
                print(f"Erreur lors du téléchargement de {model_name}.")
                GLib.idle_add(progress_bar.set_fraction, 0.0)
                break
            else:
                print(f"Progression de {model_name} : {progress * 100:.2f}%")
                GLib.idle_add(progress_bar.set_fraction, progress)

        # Mise à jour finale lorsque le téléchargement est terminé
        GLib.idle_add(progress_bar.set_text, f"{model_name} téléchargé.")
        print(f"Téléchargement terminé pour {model_name}")

    @Gtk.Template.Callback()
    def on_trash_model_clicked(self, button: Gtk.Button) -> None:
        if not self.active_toggle_button:
            self._show_toast("Aucune conversation active")
            return
        dialog = Adw.MessageDialog(
            transient_for=self,
            modal=True,
            body="Are you sure you want to quit?",
            close_response="cancel",
        )

        dialog.add_response("cancel", "_Cancel")
        dialog.add_response("delete", "Supprimer")

        dialog.set_response_appearance("delete", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self.on_trash_model_dialog_confirm)
        dialog.show()

    @Gtk.Template.Callback()
    def on_hide_conv_options(self, button: Gtk.Button):
        if self.conv_options.get_visible() == True:
            self.conv_options.set_visible(False)
            self.conv_option_set_visible.set_icon_name("go-up-symbolic")
        else:
            self.conv_options.set_visible(True)
            self.conv_option_set_visible.set_icon_name("go-down-symbolic")

    def _create_conversation_button(self, title: str) -> Gtk.ToggleButton:
        """Ajoute une conversation au panneau latéral."""
        button = Gtk.ToggleButton(label=title)
        button.conversation_id = len(self.ollama_model.get_all_conversations())
        button.connect("toggled", self.on_conversation_selected)
        self.toggle_buttons_conv.append(button)
        return button

    def on_conversation_selected(self, button: Gtk.ToggleButton) -> None:
        """Gère la sélection et le basculement des conversation."""
        if button.get_active():
            self.active_toggle_button = button
            for other_button in self.toggle_buttons_conv:
                if other_button != button:
                    other_button.set_active(False)
            conv_id = button.conversation_id
            self.is_conversation_active(conv_id)

    def on_model_selected(self, button: Gtk.ToggleButton) -> None:
        if button.get_active():
            self.active_toggle_button = button
            model_name = self.active_toggle_button.model_data['name']

            # Vérifier si un téléchargement est en cours pour ce modèle
            if model_name in self.model_progress_bars:
                progress_bar = self.model_progress_bars[model_name]
                if progress_bar.get_fraction() < 1.0:
                    # Afficher uniquement la barre de progression du modèle sélectionné
                    for bar_model, progress_bar in self.model_progress_bars.items():
                        if bar_model == model_name:
                            progress_bar.set_visible(True)
                        else:
                            progress_bar.set_visible(False)
                    return
                else:
                    print(f"Téléchargement terminé pour {model_name}.")
            else:
                # Si aucun téléchargement n'est actif, cacher toutes les barres de progression
                for progress_bar in self.model_progress_bars.values():
                    progress_bar.set_visible(False)

            # Vérifier l'état du modèle et afficher les bons boutons
            if self.active_toggle_button.model_data.get('last_updated') is not None:
                self.stack_model_buttons_options.set_visible_child(self.distant_buttons_options)
            else:
                self.stack_model_buttons_options.set_visible_child(self.local_buttons_options)

            # Désactiver les autres boutons
            for other_button in self.toggle_buttons_models:
                if other_button != button:
                    other_button.set_active(False)

            # Construire les informations du modèle
            self._build_model_infos(button.model_data)

    def _build_model_infos(self, data: list):
        if data:
            # Liste des clés autorisées à afficher
            allowed_keys = {"name", "model", "modified_at", "size", "pulls", "tags", "last_updated", "description"}
            for row in self.action_rows:
                self.model_infos.remove(row)
            self.action_rows.clear()

            for key, value in data.items():
                if key in allowed_keys:
                    label_text = {
                        "name": "Nom du modèle",
                        "model": "Modèle",
                        "modified_at": "Modifié le",
                        "size": "Taille",
                        "pulls": "Téléchargements",
                        "tags": "Tags",
                        "description": "Description"
                    }.get(key, key.capitalize())

                    # Créer une ActionRow
                    row = Adw.ActionRow(title=label_text)
                    label = Gtk.Label(label=str(value))
                    label.set_halign(Gtk.Align.END)
                    row.set_subtitle(str(value))
                    self.model_infos.add(row)
                    self.action_rows.append(row)

    def is_conversation_active(self, conv_id: int) -> None:
        conversation = self.ollama_model.get_conversation(conv_id)
        title = conversation['title']
        self.conv_title.set_label(title)
        self.load_active_model(conversation)
        self.load_conversation_to_chat(conversation)

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
        self._clear_messages()  # Réinitialiser les messages affichés

        for message in conversation["history"]:
            # Ajouter un identifiant unique au message
            message['id'] = self.generate_message_id()  # Méthode pour générer un ID unique

            # Déterminer si le message est envoyé par l'utilisateur ou l'assistant
            is_sent = message["role"] == "user"

            # Créer un widget MessageWidget pour chaque message
            message_widget = Message_Widget(message["content"], is_sent, self.delete_message, message['id'])

            # Créer un ListBoxRow pour chaque message
            list_box_row = Gtk.ListBoxRow()
            list_box_row.set_child(message_widget)

            # Ajouter le ListBoxRow à la messages_list
            self.messages_list.append(list_box_row)
            self.scroll_to_bottom()

    def generate_message_id(self) -> int:
        """Génère un ID unique pour chaque message."""
        self.message_id_counter += 1
        return self.message_id_counter
