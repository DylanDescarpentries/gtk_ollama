import os, requests, json
from ollama import Client

class Ollama_client:
    def __init__(self, api_url="http://127.0.0.1:11434") -> None:
        """
        Initialise la classe avec l'URL de base de l'API.
        :param api_url: URL de l'API pour récupérer les modèles (par défaut localhost).
        """
        self.api_url = api_url
        self.history_conv = [{'id': 1, 'model': None, 'title': 'title', 'user': 'Yo, comment ça va', 'assistant': None}]
        self.fichier_json =  os.path.expanduser("~/Documents/Programmation/conv_save/conv_save.json")

    def list_models(self) -> json:
        """
        Récupère la liste des modèles depuis l'API.
        :return: Données JSON ou un dictionnaire vide en cas d'erreur.
        """
        try:
            get_model_url = f"{self.api_url}/api/tags"

            response = requests.get(get_model_url)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des modèles : {e}")
            return {}

    def get_name_model(self) -> list:
        """
        Lit le fichier JSON fixe et extrait les noms des modèles.
        :return: Liste des noms ou une liste vide en cas d'erreur.
        """
        try:
            # obtenir le json des models
            data = self.list_models()

            # Extraire les noms des modèles
            noms = [model['name'] for model in data.get('models', []) if 'name' in model]
            return noms

        except Exception as e:
            print(f"Erreur lors de l'extraction des noms : {e}")
            return []

    def prepare_messages(self, model, history_conv, user_input):
        """
        Prépare les messages pour inclure l'historique de la conversation et le nouveau message utilisateur.
        """
        messages = []

        # Vérifier que l'historique de la conversation est bien une liste
        if isinstance(history_conv, list):
            for conv in history_conv:
                if isinstance(conv, dict) and 'history' in conv:
                    # Extraire uniquement les messages dans 'history'
                    for message in conv['history']:
                        if 'role' in message and 'content' in message:
                            messages.append({'role': message['role'], 'content': message['content']})
                        else:
                            print(f"Message mal formé dans l'historique : {message}")
                else:
                    print(f"Entrée d'historique non conforme : {conv}")

        messages.append({'role': 'user', 'content': user_input})
        return messages

    def response(self, model, user_input, history_conv):
        """
        Envoie une requête au modèle avec l'historique de la conversation et le message utilisateur.
        Args:
            model (str): Le nom du modèle utilisé.
            user_input (str): Le message de l'utilisateur.
        Returns:
            str: La réponse du modèle ou un message d'erreur.
        """
        messages = self.prepare_messages(model, history_conv, user_input)
        # Effectuer la requête au modèle
        try:
            client = Client(host=self.api_url)
            response = client.chat(model=model, messages=(messages))
            return response['message']['content']
        except Exception as e:
            print(f"Erreur lors de la requête au modèle '{model}' : {e}")
            return "Une erreur est survenue. Veuillez réessayer."

    def create_default_title(self, conversation):
        """
        Crée un titre par défaut pour une conversation.
        Le titre est basé sur les premiers mots de la requête utilisateur.
        """
        user_input = conversation.get("user", "").strip()  # Récupère la requête utilisateur
        if not user_input:
            return "Nouvelle Conversation"  # Titre par défaut si aucune requête utilisateur

        # Limite le titre à 5 mots maximum
        title = user_input[:23].rsplit(" ", 1)[0] + "..." if len(user_input) > 24 else user_input
        return title if title else "Nouvelle Conversation"
