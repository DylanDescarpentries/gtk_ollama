import os, requests, json
from ollama import Client, Options

class Ollama_client:
    def __init__(self, api_url="http://127.0.0.1:11434") -> None:
        """
        Initialise la classe avec l'URL de base de l'API.
        :param api_url: URL de l'API pour récupérer les modèles (par défaut localhost).
        """
        self.api_url = api_url

    def get_list_models(self) -> json:
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

    def get_distant_models(self, file_path=f"{os.path.expanduser('~')}/saves/ollama_models.json") -> None:
        """
        Charge les modele distant à partir d'un fichier JSON.
        Args:
            file_path (str): Le chemin du fichier contenant les données JSON.
        """
        try:
            print(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    distant_models = json.loads(content)
                    return distant_models
                else:
                    print(f"Le fichier {file_path} est vide. Initialisation avec une liste vide.")
                    distant_models = []
                    return distant_models
        except FileNotFoundError:
            print(f"Fichier {file_path} introuvable. Initialisation avec une liste vide.")
            distant_models = []
            return distant_models
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON dans le fichier {file_path} : {e}")
            distant_models = []
            return distant_models

    def get_name_model(self) -> list:
        """
        Lit le fichier JSON fixe et extrait les noms des modèles.
        :return: Liste des noms ou une liste vide en cas d'erreur.
        """
        try:
            # obtenir le json des models
            data = self.get_list_models()

            # Extraire les noms des modèles
            noms = [model['name'] for model in data.get('models', []) if 'name' in model]
            return noms

        except Exception as e:
            print(f"Erreur lors de l'extraction des noms : {e}")
            return []

    def prepare_messages(self, conversation, user_input):
        """
        Prépare les messages pour inclure l'historique de la conversation et le nouveau message utilisateur.
        """
        messages = []

        # Vérifier si un prompt système est présent dans la conversation
        if 'system' in conversation:
            messages.append({'role': 'system', 'content': conversation['system']})

        # Ajouter l'historique des messages
        if isinstance(conversation, dict) and 'history' in conversation:
            for message in conversation['history']:
                if isinstance(message, dict) and 'role' in message and 'content' in message:
                    messages.append({'role': message['role'], 'content': message['content']})
                else:
                    print(f"Message mal formé dans l'historique : {message}")

        # Ajouter le message utilisateur
        messages.append({'role': 'user', 'content': user_input})

        return messages

    def response(self, model, user_input, conversation, temp):
        """
        Envoie une requête au modèle avec l'historique de la conversation et le message utilisateur.
        Args:
            model (str): Le nom du modèle utilisé.
            user_input (str): Le message de l'utilisateur.
        Returns:
            str: La réponse du modèle ou un message d'erreur.
        """
        messages = self.prepare_messages(conversation, user_input)
        system = conversation.get('system')
        history_conv = conversation.get("history")
        options = Options(
            temperature=temp,
            system=system,
        )
        try:
            client = Client(host=self.api_url)
            response = client.chat(
                model=model,
                messages=messages,
                options=options,
            )
            return response.get('message', {}).get('content', "Réponse vide du modèle.")
        except Exception as e:
            print(f"Erreur lors de la requête au modèle '{model}' : {e}")
            return "Une erreur est survenue. Veuillez réessayer."

    def create_default_title(self, conversation) -> str:
        """
        Crée un titre par défaut pour une conversation.
        Le titre est basé sur les premiers mots de la requête utilisateur.
        """
        user_input = conversation.get("user", "").strip()
        if not user_input:
            return "Nouvelle Conversation"

        # Limite le titre à 5 mots maximum
        title = user_input[:23].rsplit(" ", 1)[0] + "..." if len(user_input) > 24 else user_input
        return title if title else "Nouvelle Conversation"

    def delete_model(self, name_model):
        url = f"{self.api_url}/api/delete"
        data = {
            "model": name_model
        }

        response = requests.delete(url, json=data)

        print(f"Statut: {response.status_code}")

    def pull_model(self, name_model):
        url = f"{self.api_url}/api/pull"
        data = {"model": name_model}
        print("URL:", url)
        print("Payload:", data)

        response = requests.post(url, json=data, stream=True)
        print("Response status:", response.status_code)

        if response.status_code != 200:
            print("Erreur lors de la requête :", response.status_code)
            yield None  # Retourne une valeur indicative en cas d'erreur
            return

        try:
            for line in response.iter_lines():
                if line:
                    try:
                        status_update = json.loads(line.decode('utf-8'))
                    except json.JSONDecodeError as e:
                        print("Erreur de décodage JSON :", e, "Ligne brute :", line)
                        continue

                    if 'total' in status_update and 'completed' in status_update:
                        total = status_update['total']
                        completed = status_update['completed']
                        if total > 0:
                            fraction = completed / total
                            yield fraction  # Retourne la progression sous forme de fraction
                        else:
                            print("Total est 0, progression non calculable.")
                    else:
                        print("Clés manquantes dans le statut :", status_update)
        except Exception as e:
            print("Erreur pendant le traitement :", e)
            yield None


