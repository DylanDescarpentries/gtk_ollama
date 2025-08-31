import gi, re, subprocess, typing, shlex
gi.require_version('Gtk', '4.0')
gi.require_version('GtkSource', '5')
from gi.repository import Gtk, Gdk, GLib, GtkSource


class Message_Widget(Gtk.Box):
    """Widget pour afficher les messages avec support des blocs de code et exécution shell."""
    
    def __init__(self, text: str, user: bool, delete_callback: callable, message_id: str) -> None:
        """
        Initialise un widget de message.
        
        Args:
            text: Contenu du message
            user: True si c'est un message utilisateur, False sinon
            delete_callback: Fonction à appeler pour supprimer le message
            message_id: Identifiant unique du message
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(15)
        self.set_margin_end(15)
        self.message_id = message_id
        self.delete_callback = delete_callback
        
        # Variables de debug et d'état
        self._debug_enabled = False  # Activé pour debug
        self._last_textview = None  # Référence au dernier TextView créé
        self._executed_blocks = set()  # Éviter les exécutions multiples
        
        self.debug_print(f"Initialisation avec texte: '{text[:50] if text else 'None'}...' (longueur: {len(text) if text else 0})")

        # Définir l'alignement principal
        self.set_halign(Gtk.Align.END if user else Gtk.Align.START)
        self.set_hexpand(True)

        # Conteneur principal pour les marges internes et le style
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        main_container.set_hexpand(True)
        self.append(main_container)

        # Appliquer les classes CSS
        self._setup_css(main_container)

        # Header : Boutons (modifier, supprimer)
        self._create_header(main_container)

        # Corps : Contenu du message avec détection de code
        self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        main_container.append(self.content_container)
        
        # Traiter et afficher le contenu
        if text and text.strip():
            self.process_and_display_content(text)
        else:
            # Si pas de texte initial, créer un TextView vide pour le streaming
            self.debug_print("Création d'un TextView vide pour streaming")
            self.add_text_view("")

    def _setup_css(self, main_container: Gtk.Box) -> None:
        """Configure les styles CSS pour le widget."""
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
                min-height: 25px;
            }
            
            .code-block {
                background: #2d3748;
                border-radius: 5px;
                padding: 10px;
                margin: 5px 0;
                font-family: 'Courier New', monospace;
            }
            
            .language-label {
                background: #4a5568;
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            """
        )
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        main_container.add_css_class("box_message")

    def _create_header(self, main_container: Gtk.Box) -> None:
        """Crée les boutons d'en-tête."""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header.set_halign(Gtk.Align.END)
        
        modify_button = Gtk.Button(label="Editer")
        delete_button = Gtk.Button(label="Supprimer")
        delete_button.set_icon_name("user-trash-symbolic")
        delete_button.connect("clicked", lambda btn: self.delete_callback(self))
        
        header.append(modify_button)
        header.append(delete_button)
        main_container.append(header)

    def debug_print(self, message: str) -> None:
        """Affiche les messages de debug si activé."""
        if self._debug_enabled:
            print(f"[Message_Widget {self.message_id}] {message}")

    def process_and_display_content(self, text: str) -> None:
        """Traite le texte pour détecter et afficher les blocs de code."""
        self.debug_print(f"Traitement du contenu: '{text[:50]}...'")
        
        # Extraire les blocs de code
        code_blocks = self.extract_docstring(text)
        
        if not code_blocks:
            # Pas de blocs de code, afficher le texte normal
            self.debug_print("Aucun bloc de code détecté")
            self.add_text_view(text)
        else:
            self.debug_print(f"Blocs de code détectés: {len(code_blocks)}")
            # Diviser le texte en parties : texte normal et blocs de code
            parts = self.split_text_with_code_blocks(text)
            
            for i, (part_type, content, lang) in enumerate(parts):
                self.debug_print(f"Partie {i}: type={part_type}, longueur={len(content)}")
                if part_type == 'text':
                    if content.strip():  # Éviter d'ajouter du texte vide
                        self.add_text_view(content)
                elif part_type == 'code':
                    self.add_code_block(content, lang)

    def split_text_with_code_blocks(self, text: str) -> list[tuple[str, str, str]]:
        """Divise le texte en alternant entre texte normal et blocs de code."""
        parts = []
        pattern = r"```(\w*)\n(.*?)```"
        
        last_end = 0
        for match in re.finditer(pattern, text, re.DOTALL):
            # Texte avant le bloc de code
            before_text = text[last_end:match.start()]
            if before_text:
                parts.append(('text', before_text, ''))
            
            # Bloc de code
            lang = match.group(1) or self._detect_language(match.group(2))
            code = match.group(2).strip()
            parts.append(('code', code, lang))
            
            # Exécution des commandes shell (éviter les doublons)
            # if lang in ["shell", "bash"] and code not in self._executed_blocks:
            #     self.debug_print(f"Nouveau bloc shell détecté: {code}")
            #     self._executed_blocks.add(code)
            #     print(f"le code a exécuter : {code}")
            #     outputs = self.execute_shell_command(code)
                
            #     # Afficher les résultats
            #     for i, output in enumerate(outputs):
            #         self.debug_print(f"Résultat shell {i+1}: {output}")
            
            last_end = match.end()
        
        # Texte après le dernier bloc de code
        remaining_text = text[last_end:]
        if remaining_text:
            parts.append(('text', remaining_text, ''))
        
        return parts

    def add_text_view(self, text: str) -> None:
        """Ajoute un TextView normal pour le texte."""
        self.debug_print(f"Création TextView avec texte: '{text[:30]}...' (longueur: {len(text)})")
        
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.add_css_class("message-textview")
        text_view.set_hexpand(True)
        text_view.set_vexpand(False)
        text_view.set_size_request(800, -1)
        
        # Définir le texte AVANT d'ajouter à l'interface
        buffer = text_view.get_buffer()
        if text:
            buffer.set_text(text)
            # Vérification
            start = buffer.get_start_iter()
            end = buffer.get_end_iter()
            actual_text = buffer.get_text(start, end, False)
            self.debug_print(f"Texte dans le buffer: '{actual_text[:30]}...' (longueur: {len(actual_text)})")
        else:
            buffer.set_text("")
        
        # Sauvegarder la référence
        self._last_textview = text_view
        
        # Ajouter à l'interface
        self.content_container.append(text_view)
        text_view.queue_draw()

    def add_code_block(self, code: str, language: str) -> None:
        """Ajoute un bloc de code avec coloration syntaxique."""
        self.debug_print(f"Création bloc de code: langage={language}, longueur={len(code)}")
        
        # Conteneur pour le bloc de code
        code_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        code_container.add_css_class("code-block")
        
        # Label du langage
        if language and language != 'text':
            lang_label = Gtk.Label(label=language.upper())
            lang_label.add_css_class("language-label")
            lang_label.set_halign(Gtk.Align.START)
            code_container.append(lang_label)
        
        # Essayer d'utiliser GtkSourceView pour la coloration syntaxique
        try:
            source_buffer = GtkSource.Buffer()
            lang_manager = GtkSource.LanguageManager()
            
            # Mapper les noms de langages
            lang_mapping = {
                'python': 'python3',
                'javascript': 'js',
                'java': 'java',
                'c': 'c',
                'cpp': 'cpp',
                'shell': 'sh',
                'bash': 'sh',
                'html': 'html',
                'css': 'css',
                'sql': 'sql'
            }
            
            gtk_lang_id = lang_mapping.get(language, language)
            gtk_language = lang_manager.get_language(gtk_lang_id)
            
            if gtk_language:
                source_buffer.set_language(gtk_language)
                source_buffer.set_highlight_syntax(True)
            
            source_buffer.set_text(code)
            
            source_view = GtkSource.View.new_with_buffer(source_buffer)
            source_view.set_editable(False)
            source_view.set_cursor_visible(False)
            source_view.set_show_line_numbers(True)
            source_view.set_highlight_current_line(False)
            source_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            source_view.set_hexpand(True)
            source_view.set_size_request(800, -1)
            
            # Appliquer un thème sombre
            scheme_manager = GtkSource.StyleSchemeManager()
            dark_scheme = scheme_manager.get_scheme('Adwaita-dark')
            if dark_scheme:
                source_buffer.set_style_scheme(dark_scheme)
            
            code_container.append(source_view)
            
        except Exception as e:
            self.debug_print(f"Erreur avec GtkSourceView, utilisation de TextView simple: {e}")
            # Fallback vers TextView simple
            code_view = Gtk.TextView()
            code_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            code_view.set_editable(False)
            code_view.set_cursor_visible(False)
            code_view.set_hexpand(True)
            code_view.set_size_request(800, -1)
            
            # Police monospace
            font_desc = code_view.get_style_context().get_font()
            font_desc.set_family("monospace")
            code_view.override_font(font_desc)
            
            code_buffer = code_view.get_buffer()
            code_buffer.set_text(code)
            
            code_container.append(code_view)
        
        self.content_container.append(code_container)

    def append_text(self, additional_text: str) -> None:
        """Ajoute du texte au contenu existant de manière optimisée pour le streaming."""
        self.debug_print(f"Ajout de texte: '{additional_text[:30]}...' (longueur: {len(additional_text)})")
        
        try:
            def update_content():
                if not additional_text:
                    self.debug_print("Texte vide reçu, ignoré")
                    return
                
                success = self._append_to_last_textview(additional_text)
                
                if not success:
                    self.debug_print("Échec de l'ajout au TextView existant, création d'un nouveau")
                    self.add_text_view(additional_text)
                
                # Détecter la fin d'un bloc de code pour le reformater
                if additional_text.endswith("```\n") or additional_text.endswith("```"):
                    self.debug_print("Fin de bloc de code détectée, programmation du reformatage")
                    GLib.timeout_add(100, self._check_and_reformat_if_needed)
            
            if not GLib.main_context_default().is_owner():
                GLib.idle_add(update_content)
            else:
                update_content()
        except Exception as e:
            self.debug_print(f"Erreur lors de l'ajout de texte: {e}")
    
    def _check_and_reformat_if_needed(self) -> bool:
        """Vérifie si le contenu actuel contient des blocs de code complets et les reformate si nécessaire."""
        try:
            current_text = self.get_current_displayed_text()
            triple_quotes = current_text.count("```")
            
            self.debug_print(f"Vérification reformatage: {triple_quotes} triple quotes trouvées")
            
            if triple_quotes >= 2 and triple_quotes % 2 == 0:
                self.debug_print("Reformatage du contenu")
                self._rebuild_content(current_text)
        except Exception as e:
            self.debug_print(f"Erreur lors du reformatage: {e}")
        
        return False  # N'exécuter qu'une fois
    
    def _append_to_last_textview(self, text: str) -> bool:
        """Ajoute du texte au dernier TextView existant."""
        self.debug_print(f"Recherche du dernier TextView pour y ajouter: '{text[:20]}...'")
        
        # Utiliser la référence sauvegardée si elle existe
        if self._last_textview and self._last_textview.get_parent():
            try:
                buffer = self._last_textview.get_buffer()
                end_iter = buffer.get_end_iter()
                buffer.insert(end_iter, text)
                
                # Vérification
                start = buffer.get_start_iter()
                end = buffer.get_end_iter()
                actual_text = buffer.get_text(start, end, False)
                self.debug_print(f"Texte ajouté avec succès. Buffer contient maintenant {len(actual_text)} caractères")
                
                self._last_textview.queue_draw()
                return True
            except Exception as e:
                self.debug_print(f"Erreur avec la référence sauvegardée: {e}")
                self._last_textview = None
        
        # Fallback : chercher le dernier TextView dans le conteneur
        last_textview = None
        child = self.content_container.get_first_child()
        
        while child:
            if isinstance(child, Gtk.TextView):
                last_textview = child
                self.debug_print("TextView trouvé")
            child = child.get_next_sibling()
        
        if last_textview:
            try:
                buffer = last_textview.get_buffer()
                end_iter = buffer.get_end_iter()
                buffer.insert(end_iter, text)
                
                # Sauvegarder la référence
                self._last_textview = last_textview
                
                # Vérification
                start = buffer.get_start_iter()
                end = buffer.get_end_iter()
                actual_text = buffer.get_text(start, end, False)
                self.debug_print(f"Texte ajouté au TextView existant. Buffer contient maintenant {len(actual_text)} caractères")
                
                last_textview.queue_draw()
                return True
            except Exception as e:
                self.debug_print(f"Erreur lors de l'ajout au TextView existant: {e}")
                return False
        else:
            self.debug_print("Aucun TextView existant trouvé")
            return False
    
    def _rebuild_content(self, full_text: str) -> None:
        """Reconstruit le contenu complet seulement quand nécessaire."""
        self.debug_print("Reconstruction complète du contenu")
        
        # Réinitialiser les références
        self._last_textview = None
        self._executed_blocks.clear()
        
        # Vider le conteneur
        child = self.content_container.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.content_container.remove(child)
            child = next_child
        
        # Reconstruire
        self.process_and_display_content(full_text)
    
    def get_current_displayed_text(self) -> str:
        """Récupère le texte actuellement affiché."""
        full_text = ""
        child = self.content_container.get_first_child()
        
        while child:
            if isinstance(child, Gtk.TextView):
                buffer = child.get_buffer()
                start = buffer.get_start_iter()
                end = buffer.get_end_iter()
                text_content = buffer.get_text(start, end, False)
                full_text += text_content
                self.debug_print(f"TextView lu: {len(text_content)} caractères")
            elif isinstance(child, Gtk.Box):
                # Chercher le TextView/SourceView dans le bloc de code
                code_child = child.get_first_child()
                while code_child:
                    if isinstance(code_child, (Gtk.TextView, GtkSource.View)):
                        buffer = code_child.get_buffer()
                        start = buffer.get_start_iter()
                        end = buffer.get_end_iter()
                        code_text = buffer.get_text(start, end, False)
                        # Reconstituer le bloc de code avec les marqueurs ```
                        full_text += f"```\n{code_text}\n```"
                        break
                    code_child = code_child.get_next_sibling()
            
            child = child.get_next_sibling()
        
        self.debug_print(f"Texte total récupéré: {len(full_text)} caractères")
        return full_text

    def get_current_text(self) -> str:
        """Récupère le texte complet actuellement affiché."""
        return self.get_current_displayed_text()
    
    def finalize_streaming(self) -> None:
        """Finalise le streaming en reformatant le contenu final."""
        self.debug_print("Finalisation du streaming")
        try:
            current_text = self.get_current_displayed_text()
            if "```" in current_text:
                self.debug_print("Blocs de code détectés, reformatage final")
                self._rebuild_content(current_text)
            else:
                self.debug_print("Pas de blocs de code, pas de reformatage nécessaire")
        except Exception as e:
            self.debug_print(f"Erreur lors de la finalisation: {e}")

    def extract_docstring(self, text: str) -> list[tuple[str, str]]:
        """Extrait tous les blocs de texte situés entre ``` dans une chaîne donnée."""
        pattern = r"```(\w*)\n(.*?)```"
        blocks = re.findall(pattern, text, re.DOTALL)
        
        processed_blocks = []
        for lang, code in blocks:
            code = code.strip()
            if not code:
                continue
                
            if not lang:
                detected_lang = self._detect_language(code)
                self.debug_print(f"Langage détecté: {detected_lang}")
                lang = detected_lang
            
            processed_blocks.append((code, lang))
        
        return processed_blocks

    def _detect_language(self, code: str) -> str:
        """Détecte le langage de programmation à partir du contenu du code."""
        indicators = {
            'python': [
                'import ', 'from ', 'def ', 'class ', 'print(', 'return ',
                'if __name__ == "__main__":', '# ', 'else:', 'elif ', 'try:',
                'except:', 'finally:', 'with ', 'as ', 'lambda ', 'yield ',
                'range(', 'len(', 'str(', 'int(', 'list(', 'dict(',
            ],
            'javascript': [
                'function ', 'var ', 'let ', 'const ', 'console.log(',
                '=>', 'document.', 'window.', '$(', 'require(', 'module.exports',
                'async ', 'await ', '.then(', '.catch(', 'JSON.', 'Array.',
            ],
            'shell': [
                '#!/bin/bash', '#!/bin/sh', 'mkdir ', 'cd ', 'ls ', 'echo ',
                'sudo ', 'apt ', 'yum ', 'chmod ', 'chown ', 'grep ', 'awk ',
                'sed ', 'curl ', 'wget ', 'export ', '$1', '$2', '${', 'fi',
                'touch ', 'rm ', 'cp ', 'mv ', 'cat ', 'head ', 'tail ',
            ],
        }
        
        code_lower = code.lower()
        scores = {lang: 0 for lang in indicators}
        
        for lang, patterns in indicators.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                count = code_lower.count(pattern_lower)
                scores[lang] += count
        
        if any(scores.values()):
            best_lang = max(scores.items(), key=lambda x: x[1])
            language = best_lang[0]
            self.debug_print(f"Langage détecté: {language}")
            return language
        
        return 'text'

    # CORRECTION PRINCIPALE: Méthode execute_shell_command complètement refaite
    def execute_shell_command(self, commands: typing.Union[str, list[str]]) -> list[str]:
        """
        Exécute des commandes shell sur l'hôte Fedora Linux via flatpak-spawn.
        
        Args:
            commands: Commande(s) à exécuter:
                - str: commande unique ou bloc multi-lignes
                - list[str]: liste de commandes
        
        Returns:
            list[str]: Liste des sorties de chaque commande
        """
        # Normaliser l'entrée
        command_list = self._normalize_commands_input(commands)
        
        if not command_list:
            self.debug_print("Aucune commande valide à exécuter")
            return ["Aucune commande valide"]
        
        outputs = []
        
        # Détecter si on a besoin d'exécuter en séquence (avec cd)
        has_cd_command = any(cmd.strip().startswith('cd ') for cmd in command_list)
        
        if has_cd_command and len(command_list) > 1:
            # Exécuter toutes les commandes dans un seul processus bash
            return self._execute_sequential_commands(command_list)
        else:
            # Exécuter chaque commande séparément
            return self._execute_individual_commands(command_list)

    def _normalize_commands_input(self, commands: typing.Union[str, list[str]]) -> list[str]:
        """Normalise l'entrée en liste de commandes valides."""
        if isinstance(commands, str):
            if '\n' in commands:
                # Bloc multi-lignes
                self.debug_print("Bloc multi-lignes détecté, parsing...")
                lines = commands.strip().split('\n')
                command_list = []
                
                for line in lines:
                    line = line.strip()
                    # Ignorer les commentaires, les lignes vides et les shebangs
                    if line and not line.startswith('#') and not line.startswith('!'):
                        command_list.append(line)
                
                return command_list
            else:
                # Commande unique
                command = commands.strip()
                return [command] if command else []
                
        elif isinstance(commands, list):
            # Déjà une liste, filtrer les commandes vides
            return [cmd.strip() for cmd in commands if cmd and cmd.strip()]
        else:
            self.debug_print(f"Type d'entrée non supporté: {type(commands)}")
            return []

    def _execute_sequential_commands(self, commands: list[str]) -> list[str]:
        """Exécute les commandes en séquence dans le même processus bash."""
        try:
            # Combiner toutes les commandes avec &&
            combined_command = " && ".join(commands)
            
            self.debug_print(f"Exécution séquentielle: {combined_command}")
            
            # CORRECTION: Passer la commande comme un seul argument string
            host_command = ["flatpak-spawn", "--host", "bash", "-c", combined_command]
            
            result = subprocess.run(
                host_command,
                shell=False,
                text=True,
                capture_output=True,
                check=False,
                timeout=60
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return [output if output else "Commandes exécutées avec succès"]
            else:
                error_msg = result.stderr.strip()
                return [f"Erreur lors de l'exécution séquentielle: {error_msg}"]
                
        except Exception as e:
            return [f"Exception lors de l'exécution séquentielle: {str(e)}"]

    def _execute_individual_commands(self, commands: list[str]) -> list[str]:
        """Exécute chaque commande individuellement via bash."""
        outputs = []
        
        for command in commands:
            try:
                self.debug_print(f"Exécution individuelle: '{command}'")
                
                # CORRECTION: Passer la commande comme un seul argument string
                # PAS comme une liste de caractères !
                host_command = ["flatpak-spawn", "--host", "bash", "-c", command]
                
                result = subprocess.run(
                    host_command,
                    shell=False,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=30
                )
                
                self._debug_print("retour du code commande : ", result.returncode)
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    self.debug_print(f"Succès: '{output}'")
                    outputs.append(output if output else "Commande exécutée avec succès (pas de sortie)")
                else:
                    error_msg = result.stderr.strip()
                    self.debug_print(f"Erreur (code {result.returncode}): {error_msg}")
                    outputs.append(f"Erreur (code {result.returncode}): {error_msg}")
                    
            except subprocess.TimeoutExpired:
                outputs.append(f"Timeout lors de l'exécution de '{command}'")
            except Exception as e:
                outputs.append(f"Exception lors de l'exécution de '{command}': {str(e)}")
        
        return outputs

    def get_message_id(self) -> str:
        """Retourne l'ID du message."""
        return self.message_id

    # Méthodes de commodité
    def execute_single_command(self, command: str) -> str:
        """Exécute une seule commande et retourne sa sortie."""
        results = self.execute_shell_command(command)
        return results[0] if results else "Aucun résultat"
    
    def execute_command_block(self, code_block: str) -> list[str]:
        """Exécute un bloc de commandes multi-lignes."""
        return self.execute_shell_command(code_block)
    
    def test_permissions(self) -> None:
        """Teste les permissions flatpak-spawn."""
        tests = [
            "whoami",
            "pwd", 
            "echo $HOME",
            "ls -la $HOME",
            "mkdir -p /tmp/test_flatpak",
            "ls -la /tmp/ | grep test_flatpak"
        ]
        
        print("=== Test des permissions flatpak-spawn ===")
        for cmd in tests:
            result = self.execute_shell_command(cmd)
            print(f"{cmd} → {result[0]}")