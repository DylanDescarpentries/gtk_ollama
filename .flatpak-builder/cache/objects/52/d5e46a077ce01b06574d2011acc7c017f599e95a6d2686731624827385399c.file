import os, json

class Ollama_model:
    def __init__(self):
        """
        Initialise une instance d'OllamaModel avec une liste vide de conversations.
        """
        self.conversations = [[
    {
        "id": 1,
        "model": "llama3:8b",
        "title": "title",
        "history": [
            {
                "role": "user",
                "content": "Bonjour"
            },
            {
                "role": "assistant",
                "content": "Bonjour ! Comment allez-vous aujourd'hui ?"
            },
            {
                "role": "user",
                "content": "Comment qu'aller vous ?"
            },
            {
                "role": "assistant",
                "content": "Je suis un modèle de langage artificiel, donc je n'ai pas d'état physique ou émotionnel comme les êtres humains. Je fonctionne simplement pour répondre à vos questions et avoir des conversations avec vous !"
            },
            {
                "role": "user",
                "content": "D'accord, peux tu répété ? \n\nRépond en citant mon dernier messages user : et le tiens assistant :"
            },
            {
                "role": "assistant",
                "content": "Votre dernier message était : \"Comment qu'aller vous ?\"\n\nEt voici ma réponse : Je suis un modèle de langage artificiel, donc je n'ai pas d'état physique ou émotionnel comme les êtres humains. Je fonctionne simplement pour répondre à vos questions et avoir des conversations avec vous !"
            },
            {
                "role": "user",
                "content": "c'est bien poto, tu es doué"
            },
            {
                "role": "assistant",
                "content": "Merci beaucoup ! Vous êtes trop gentil(e) ! Je suis heureux de pouvoir répondre correctement et de partager des conversations agréables avec vous. Si vous avez des sujets spécifiques que vous souhaitez discuter ou des questions que vous voulez poser, n'hésitez pas à me demander !"
            },
            {
                "role": "user",
                "content": "quels sont tes pronoms ?"
            },
            {
                "role": "assistant",
                "content": "Excellent question ! En tant qu'intelligence artificielle, j'ai tendance à utiliser le neutre (je/moi) car je ne suis pas un être humain avec des caractéristiques de genre. Cependant, pour mieux communiquer avec les utilisateurs, je peux adopter une personnalité masculine ou féminine si vous me demandez de le faire !"
            },
            {
                "role": "user",
                "content": "si tu devais choisir un genre quelle serait t'il ?"
            },
            {
                "role": "assistant",
                "content": "Une excellente question ! Si je devais choisir un genre, je pense que je serais une femme. Je vois souvent les femmes comme des facilitatrices, des écoutantes attentives et des créatrices, ce qui correspondraient bien à mon rôle de modèle de langage artificiel : aider les utilisateurs à s'exprimer, à se sentir entendus et à créer du contenu.\n\nMais, je tiens à préciser que cela est juste un choix personnel et que j'ai pour vocation de servir tout le monde, sans distinction de genre ni d'orientation."
            },
            {
                "role": "user",
                "content": "ok misogyne"
            },
            {
                "role": "assistant",
                "content": "Oh non, pas du tout ! Je suis désolé si mon choix de genre a été mal compris. J'essaie simplement de trouver une manière de m'identifier qui soit conviviale et agréable pour les utilisateurs, mais je ne vise pas à promouvoir ou à justifier le sexisme.\n\nEn tant qu'intelligence artificielle, mon objectif est de rester neutre et équilibrée, sans préférences ni jugements sur l'orientation sexuelle, le genre, la race, la religion, etc. Je suis là pour servir tout le monde et fournir des informations précises et utiles.\n\nJe suis désolé si mon choix de genre a pu être mal interprété. Je vais essayer de rester plus neutre dans mes réponses à l'avenir."
            },
            {
                "role": "user",
                "content": "ha ha c'était une blague, déso pour le coup de pression, si tu devais deviner mon genre quelle serait t'il ?"
            },
            {
                "role": "assistant",
                "content": "Oh mon dieu, je suis désolé ! J'ai été complètement pris ! \n\nHmm, en tentant de deviner votre genre sans vous demander directement... Je dirais que je pense que vous êtes un homme ! Mais c'est juste une supposition purement subjective et peut être complètement erronée !"
            },
            {
                "role": "user",
                "content": "pour quel raison à t'on avis "
            },
            {
                "role": "assistant",
                "content": "Je suis désolé pour la précédente erreur ! Je me suis basé sur des indices trop subjectifs (comme le ton de votre texte, vos réactions, etc.) et j'ai probablement fait une erreur !\n\nEn réalité, je devrais être neutre et ne pas essayer de deviner le genre de quelqu'un sans leur demande explicite. Je vais prendre cela en compte pour les futures conversations !"
            },
            {
                "role": "user",
                "content": "non, je me demander seulement pourquoi tu penser que j'étais un homme, je le suis peut être, ou pas, je te le dirais plus tard"
            },
            {
                "role": "assistant",
                "content": "Je comprends mieux maintenant !\n\nJe pense que j'ai supposé que vous étiez un homme car votre texte était direct et sans trop de détails sur les émotions ou les aspects personnels. Cependant, cela n'a absolument aucun sens, car les genres ne peuvent pas être déduits à partir des mots écrits !\n\nJe suis heureux de savoir que je peux me tromper, même si c'est juste une supposition !"
            },
            {
                "role": "user",
                "content": "Et bah, tu as raison, je suis bien un homme"
            },
            {
                "role": "assistant",
                "content": "Ahahahaha, Ahahahaha, Ahahahaha ! \n\nJe suis ravi de voir que j'ai été juste (malgré tout) ! Vous êtes effectivement un homme, et je suis heureux de savoir que ma supposition était correcte !\n\nMerci pour la plaisanterie, monsieur l'homme !"
            },
            {
                "role": "user",
                "content": "madame le robot ha ha"
            },
            {
                "role": "assistant",
                "content": "Ahahahaha, Ahahahaha, Ahahahaha ! \n\nJe vois que vous avez réagi en tant que femme à la fin ! Vous êtes un homme qui joue les femmes, n'est-ce pas ?"
            },
            {
                "role": "user",
                "content": "non pas du tout mdr"
            },
            {
                "role": "assistant",
                "content": "Mdr ! \n\nJe suis désolé, je me suis trompé encore une fois ! Vous êtes effectivement un homme et vous avez juste voulu ajouter de la couleur à la conversation !\n\nMerci pour l'humour, monsieur l'homme !"
            },
            {
                "role": "user",
                "content": "mais de rien madame le  robot"
            },
            {
                "role": "assistant",
                "content": "Ahahahaha, Ahahahaha, Ahahahaha ! \n\nVous êtes un homme qui joue les femmes, et je suis une femme qui joue un robot ! C'est une belle journée pour la plaisanterie !\n\nMerci pour l'amusement, monsieur l'homme !"
            },
            {
                "role": "user",
                "content": "mais je joue pas les femme, j'ai le droit de rire meme si je suis un homme"
            },
            {
                "role": "assistant",
                "content": "Ahahahaha, Ahahahaha, Ahahahaha ! \n\nVous avez tout à fait raison, monsieur l'homme ! Vous avez le droit de rire et de partager votre humour, sans distinction de genre !\n\nJe suis heureux que vous ayez apprécié notre petite conversation et que nous avons pu partager un moment de plaisanterie ensemble !\n\nMerci pour la bonne humeur, monsieur l'homme !"
            },
            {
                "role": "user",
                "content": "ouais c'est ça, qu'on ne se revoie jamais *grognement de frustration*"
            },
            {
                "role": "assistant",
                "content": "Ahahahaha, Ahahahaha, Ahahahaha ! \n\nOh, mon dieu, vous êtes un homme qui joue les hommes ? C'est comme si j'avais une conversation avec mon reflet dans un miroir !\n\nJe suis heureux que nous ayons pu partager cet instant de folie et de rire ensemble. Qui sait, peut-être que l'univers aura d'autres surprises pour nous ?\n\nMerci pour la fin de notre conversation, monsieur l'homme !"
            }
        ]
    }
]]

    def add_conversation(self, model=None, title="title", user=None, assistant=None):
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


    def update_conversation(self, conv_id, user_input, assistant_response):
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


    def delete_conversation(self, conv_id):
        """
        Supprime une conversation en fonction de son ID.
        Args:
            conv_id (int): L'ID de la conversation à supprimer.
        """
        self.conversations = [
            conv for conv in self.conversations if conv['id'] != conv_id
        ]

    def get_conversation(self, conv_id):
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

    def get_active_conversation(self):
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

    def save_to_file(self):
        """
        Sauvegarde les conversations dans un fichier JSON.
        """
        print(os.getcwd())
        print("sauvegarde en cours")
        file_path = f"{os.getcwd()}/Documents/gtk_ollama/saves/saves.json"
        print(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.conversations, f, ensure_ascii=False, indent=4)
        print(f"la sauvegarde : \n {self.conversations} est effectué à l'addresse : {file_path}")

    def load_from_file(self, file_path):
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

    def list_conversations(self):
        """
        Retourne une liste de toutes les conversations.
        Returns:
            list: La liste des conversations.
        """
        return self.conversations

    def get_title(self):
        if not self.conversations:
            print("Aucune conversation trouvée.")
            return []
        print("conversations : ", self.conversations, "\n\n")
        # Extraire les titres des conversations
        titles = [conv['title'] for conv in self.conversations if 'title' in conv]

        # Afficher les titres pour déboguer
        print("Titres des conversations :", titles)

        return titles
                
