import gi, re, subprocess, typing
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

class Message_Widget(Gtk.Box):
    def __init__(self, text, user, delete_callback, message_id) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(15)
        self.set_margin_end(15)
        self.message_id = message_id
        self.delete_callback = delete_callback

        # Définir l'alignement principal
        self.set_halign(Gtk.Align.END if user else Gtk.Align.START)
        # Permettre l'expansion horizontale du widget
        self.set_hexpand(True)

        # Conteneur principal pour les marges internes et le style
        main_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=5
        )
        # Permettre l'expansion horizontale du conteneur principal
        main_container.set_hexpand(True)
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

            .message-textview {
                background: transparent;
                color: inherit;
            }
            """
        )
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        main_container.add_css_class("box_message")
        # main_container.add_css_class("message-user" if user else "message-received")

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

        # Corps : Texte du message avec TextView
        self.message_view = Gtk.TextView()
        self.message_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.message_view.set_editable(False)
        self.message_view.set_cursor_visible(False)
        self.message_view.add_css_class("message-textview")
        self.message_view.set_vexpand(True)
        self.message_view.set_hexpand(True)
        # Forcer une largeur minimale pour le TextView
        self.message_view.set_size_request(800, -1)
        
        # Configurer le buffer et insérer le texte
        self.buffer = self.message_view.get_buffer()
        self.buffer.set_text(text)
        
        main_container.append(self.message_view)

    def on_delete_clicked(self, button) -> None:
        """Callback pour le bouton supprimer."""
        if self.delete_callback:
            self.delete_callback(self)

    def get_message_id(self):
        return self.message_id

    def append_text(self, additional_text: str):
        """Ajoute du texte au contenu existant."""
        try:
            end_iter = self.buffer.get_end_iter()
            self.buffer.insert(end_iter, additional_text)
        except Exception as e:
            print(f"Erreur lors de l'ajout de texte: {e}")
        
    def extract_docstring(self, text: str) -> list[str]:
        """Extrait tous les blocs de texte situés entre ``` dans une chaîne donnée."""
        # Pattern pour capturer le langage et le code entre ``` et ```
        pattern = r"```(\w*)\n(.*?)```"
        
        # Utilisation de re.findall pour récupérer tous les blocs correspondants
        blocks = re.findall(pattern, text, re.DOTALL)
        
        # Traiter chaque bloc pour déterminer son langage
        processed_blocks = []
        for lang, code in blocks:
            code = code.strip()
            if not code:
                continue
                
            # Si le langage n'est pas spécifié, essayer de le détecter
            if not lang:
                lang = self._detect_language(code)
                
            processed_blocks.append((code, lang))
            
        if processed_blocks:
            return processed_blocks
        return []

    def _detect_language(self, code: str) -> str:
        """Détecte le langage de programmation à partir du contenu du code."""
        # Indicateurs simples pour différents langages
        indicators = {
            'python': [
                'import ', 'def ', 'print(', 'return ', 'class ', 
                'if __name__ == "__main__":', '#'
            ],
            'java': [
                'public class', 'private', 'protected', 'void ', 
                'System.out.println', ';', 'import java.'
            ],
            'shell': [
                'mkdir', 'cd ', 'ls ', 'echo ', 'sudo ', 'apt ', 
                'yum ', 'chmod', 'chown', '#!/bin/bash'
            ],
            'c': [
                '#include', 'int main(', 'printf(', 'scanf(',
                'void ', 'struct ', 'typedef'
            ]
        }
        
        # Compter les occurrences d'indicateurs pour chaque langage
        scores = {lang: 0 for lang in indicators}
        
        for lang, patterns in indicators.items():
            for pattern in patterns:
                if pattern in code:
                    scores[lang] += 1
        
        print("recherche du langage...")
        # Retourner le langage avec le score le plus élevé
        if any(scores.values()):
            language = max(scores.items(), key=lambda x: x[1])[0]
            print("language : ", language)
            return max(scores.items(), key=lambda x: x[1])[0]
        print("aucun langage trouvé")
        # Par défaut, considérer comme du shell si aucun langage n'est clairement identifié
        return 'shell'

    def execute_shell_command(self, commands: list[str]) -> list[str]:
        """Exécute une liste de commandes shell sur l'hôte Fedora Linux et renvoie leurs sorties."""
        outputs = []
        for command in commands:
            try:
                # Construction de la commande avec plus de sécurité
                host_command = ["flatpak-spawn", "--host"]
                host_command.extend(command.split())
                
                # Exécution de la commande sans shell=True pour plus de sécurité
                result = subprocess.run(
                    host_command,
                    shell=False,
                    text=True,
                    capture_output=True,
                    check=False  # Ne pas lever d'exception en cas d'erreur
                )
                
                if result.returncode == 0:
                    outputs.append(result.stdout.strip())
                else:
                    print(f"Erreur lors de l'exécution de '{command}': {result.stderr}")
                    outputs.append(f"Erreur: {result.stderr}")
                    
            except Exception as e:
                print(f"Exception lors de l'exécution de '{command}': {str(e)}")
                outputs.append(f"Erreur: {str(e)}")
        
        return outputs
