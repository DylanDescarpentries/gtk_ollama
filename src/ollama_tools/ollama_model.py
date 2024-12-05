import os, json

class Ollama_model:
    def __init__(self) -> None:
        """
        Initialise une instance d'OllamaModel avec une liste vide de conversations.
        """
        self.conversations = [
        ]

    def add_conversation(self, model, title, user, assistant) -> None:
        """
        Ajoute une nouvelle conversation à la liste avec un historique structuré.
        """
        new_id = len(self.conversations) + 1
        self.conversations.append({
            'id': new_id,
            'model': model,
            'title': title,
            'history': [
                {'role': 'user', 'content': user},
                {'role': 'assistant', 'content': assistant},
            ]
        })

    def get_all_conversations(self) -> list:
        """
        Retourne une liste de toutes les conversations sous forme de dictionnaires contenant 'id' et 'title'.
        """
        if not hasattr(self, 'conversations') or not self.conversations:
            return []  # Retourne une liste vide si aucune conversation n'existe

        return [{'id': conv['id'], 'title': conv['title']} for conv in self.conversations]

    def set_active_conversation(self, conv_id) -> list:
        """
        Récupère la conversation active ou retourne la conversation par défaut avec l'ID 1.
        """
        # Rechercher une conversation marquée comme active
        for conv in self.conversations:
            if conv.get('active', False):  # Cherche une clé "active"
                return conv

        # Si aucune conversation active n'est trouvée, retourner celle avec l'ID 1
        for conv in self.conversations:
            if conv.get('id') == 1:
                return conv
        # Si aucune conversation avec l'ID 1 n'existe, retourner None
        return None

    def update_conversation(self, conv_id: int, user_input: str, assistant_response: str) ->bool:
        """
        Met à jour une conversation existante en ajoutant les nouveaux messages à l'historique.
        """
        for conv in self.conversations:
            if conv['id'] == conv_id:
                if 'history' not in conv:
                    conv['history'] = []  # Initialiser l'historique s'il n'existe pas
                conv['history'].append({'role': 'user', 'content': user_input})
                conv['history'].append({'role': 'assistant', 'content': assistant_response})
                return True
        return False

    def delete_conversation(self, conv_id: int) -> None:
        """
        Supprime une conversation en fonction de son ID.
        Args:
            conv_id (int): L'ID de la conversation à supprimer.
        """
        # Vérifier si une conversation avec cet ID existe
        conversation_to_delete = next(
            (conv for conv in self.conversations if conv['id'] == conv_id), None
        )

        if conversation_to_delete:
            self.conversations = [
                conv for conv in self.conversations if conv['id'] != conv_id
            ]
            print(f"Conversation avec l'ID {conv_id} supprimée avec succès.")
            self.save_to_file()
        else:
            print(f"Aucune conversation trouvée avec l'ID {conv_id}.")


    def get_conversation(self, conv_id: int) -> int:
        """
        Récupère une conversation en fonction de son ID.
        Args:
            conv_id (int): L'ID de la conversation à récupérer.
        Returns:
            dict: La conversation correspondante ou None si non trouvée.
        """
        for conv in self.conversations:
            if conv['id'] == conv_id:
                return conv
        return None

    def get_all_conversations(self) -> list:
        """
        Retourne une liste de toutes les conversations avec leurs 'id', 'title' et 'history'.
        """
        if not hasattr(self, 'conversations') or not self.conversations:
            return []  # Retourne une liste vide si aucune conversation n'existe

        # Récupère toutes les données nécessaires
        return [
            {
                'id': conv['id'],
                'title': conv['title'],
                'history': conv['history']  # Inclut l'historique complet
            }
            for conv in self.conversations
        ]

    def save_to_file(self) -> None:
        """
        Sauvegarde les conversations dans un fichier JSON.
        """
        print("sauvegarde en cours")
        file_path = f"{os.getcwd()}/Documents/gtk_ollama/saves/saves.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.conversations, f, ensure_ascii=False, indent=4)

    def load_from_file(self, file_path="/home/dylan/Documents/gtk_ollama/saves/saves.json") -> None:
        """
        Charge les conversations à partir d'un fichier JSON.
        Args:
            file_path (str): Le chemin du fichier contenant les données JSON.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.conversations = json.load(f)
        except FileNotFoundError:
            self.conversations = []

    def list_conversations(self) -> list:
        """
        Retourne une liste de toutes les conversations.
        Returns:
            list: La liste des conversations.
        """
        return self.conversations


