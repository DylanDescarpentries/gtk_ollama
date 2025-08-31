import pygame # type: ignore
import os
import tempfile
import platform
import time
from gradio_client import Client
from typing import Dict, Any, Optional, Generator


class TTSManager:
    """
    Gestionnaire de synthèse vocale (Text-to-Speech) utilisant Kokoro-TTS.
    Cette classe s'interface avec Ollama_client pour convertir les réponses en audio.
    """
    
    def __init__(self, tts_client_id="panyanyany/Kokoro-TTS"):
        """
        Initialise le gestionnaire TTS.
        
        Args:
            tts_client_id: ID du client Gradio pour Kokoro-TTS
        """
        self.tts_client_id = tts_client_id
        self.tts_client = None
        self._init_audio_system()
    
    def _init_audio_system(self):
        """Initialise le système audio pygame."""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.audio_system = "pygame"
            print("✅ Système audio pygame initialisé")
        except Exception as e:
            print(f"⚠️ Impossible d'initialiser pygame: {e}")
            self.audio_system = "system"
    
    def _get_tts_client(self) -> Client:
        """Récupère ou crée le client TTS."""
        if self.tts_client is None:
            try:
                self.tts_client = Client(self.tts_client_id)
                print("✅ Client Kokoro-TTS initialisé")
            except Exception as e:
                print(f"❌ Erreur lors de l'initialisation du client TTS: {e}")
                raise
        return self.tts_client
    
    def clean_text_for_tts(self, text: str, max_length: int = 1000) -> str:
        """
        Nettoie le texte pour améliorer la synthèse vocale.
        
        Args:
            text: Texte à nettoyer
            max_length: Longueur maximale du texte
            
        Returns:
            Texte nettoyé
        """
        replacements = {
            '*': '',           # Enlever les astérisques de markdown
            '#': '',           # Enlever les hashtags de markdown
            '```': '',         # Enlever les blocs de code
            '`': '',           # Enlever le code inline
            '\n\n': '. ',      # Remplacer double retour ligne par point
            '\n': ' ',         # Remplacer retour ligne par espace
            '  ': ' ',         # Réduire les espaces multiples
            '[': '',           # Enlever crochets
            ']': '',
            '(': '',           # Enlever parenthèses si nécessaire
            ')': '',
        }
        
        clean_text = text
        for old, new in replacements.items():
            clean_text = clean_text.replace(old, new)
        
        # Limiter la longueur
        if len(clean_text) > max_length:
            # Couper au dernier point ou espace avant la limite
            cut_pos = clean_text.rfind('.', 0, max_length)
            if cut_pos == -1:
                cut_pos = clean_text.rfind(' ', 0, max_length)
            if cut_pos == -1:
                cut_pos = max_length
            
            clean_text = clean_text[:cut_pos] + "..."
            print(f"📝 Texte tronqué à {cut_pos} caractères pour la synthèse vocale")
        
        return clean_text.strip()
    
    def generate_audio(self, text: str, voice: str = "af_heart", speed: float = 1.0) -> Optional[str]:
        """
        Génère un fichier audio à partir du texte.
        
        Args:
            text: Texte à synthétiser
            voice: Voix à utiliser
            speed: Vitesse de lecture
            
        Returns:
            Chemin vers le fichier audio généré ou None en cas d'erreur
        """
        try:
            print("🎤 Génération de l'audio avec Kokoro-TTS...")
            
            # Nettoyer le texte
            clean_text = self.clean_text_for_tts(text)
            
            if not clean_text.strip():
                print("❌ Texte vide après nettoyage")
                return None
            
            # Générer l'audio
            client = self._get_tts_client()
            result = client.predict(
                text=clean_text,
                voice=voice,
                speed=speed,
                api_name="/predict"
            )
            
            print(f"✅ Audio généré: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération audio: {e}")
            return None
    
    def play_audio_file(self, file_path: str) -> bool:
        """
        Lit le fichier audio.
        
        Args:
            file_path: Chemin vers le fichier audio
            
        Returns:
            True si la lecture s'est bien passée, False sinon
        """
        if not os.path.exists(file_path):
            print(f"❌ Fichier audio introuvable: {file_path}")
            return False
        
        if self.audio_system == "pygame":
            return self._play_with_pygame(file_path)
        else:
            return self._play_with_system(file_path)
    
    def _play_with_pygame(self, file_path: str) -> bool:
        """Lit l'audio avec pygame."""
        try:
            print(f"🔊 Lecture avec pygame: {os.path.basename(file_path)}")
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Attendre que la lecture soit terminée
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            print("✅ Lecture terminée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur pygame: {e}")
            return self._play_with_system(file_path)  # Fallback
    
    def _play_with_system(self, file_path: str) -> bool:
        """Lit l'audio avec les commandes système."""
        try:
            system = platform.system()
            print(f"🔊 Lecture système ({system}): {os.path.basename(file_path)}")
            
            if system == "Windows":
                os.system(f'start "" "{file_path}"')
            elif system == "Darwin":  # macOS
                os.system(f'afplay "{file_path}"')
            elif system == "Linux":
                # Essayer plusieurs lecteurs
                commands = [
                    f'paplay "{file_path}"',
                    f'aplay "{file_path}"',
                    f'ffplay -nodisp -autoexit "{file_path}"',
                    f'vlc --play-and-exit "{file_path}"'
                ]
                
                success = False
                for cmd in commands:
                    if os.system(f"{cmd} 2>/dev/null") == 0:
                        success = True
                        break
                
                if not success:
                    print("❌ Aucun lecteur audio trouvé sur ce système Linux")
                    return False
            else:
                print(f"❌ Système {system} non supporté")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lecture système: {e}")
            return False
    
    def text_to_speech_and_play(self, text: str, voice: str = "af_heart", speed: float = 1.0, auto_play: bool = True) -> Dict[str, Any]:
        """
        Méthode principale: génère l'audio et le lit automatiquement.
        
        Args:
            text: Texte à synthétiser
            voice: Voix à utiliser
            speed: Vitesse de lecture
            auto_play: Jouer automatiquement l'audio généré
            
        Returns:
            Dictionnaire avec les résultats
        """
        result = {
            'text': text,
            'audio_file': None,
            'success': False,
            'played': False,
            'error': None
        }
        
        try:
            # Générer l'audio
            audio_file = self.generate_audio(text, voice, speed)
            
            if audio_file:
                result['audio_file'] = audio_file
                result['success'] = True
                
                # Lire l'audio si demandé
                if auto_play:
                    result['played'] = self.play_audio_file(audio_file)
                    
            else:
                result['error'] = "Échec de la génération audio"
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Erreur dans text_to_speech_and_play: {e}")
        
        return result
    
    def process_ollama_stream_with_tts(self, ollama_client, model: str, user_input: str, 
                                     conversation: Dict, temp: float = 0.7, 
                                     voice: str = "af_heart", speed: float = 1.0,
                                     auto_play: bool = True) -> Dict[str, Any]:
        """
        Traite un stream Ollama et génère la synthèse vocale.
        
        Args:
            ollama_client: Instance de Ollama_client
            model: Modèle à utiliser
            user_input: Input utilisateur
            conversation: Conversation context
            temp: Température
            voice: Voix TTS
            speed: Vitesse TTS
            auto_play: Lecture automatique
            
        Returns:
            Dictionnaire avec les résultats
        """
        print("🤖 Génération de la réponse avec Ollama...")
        
        # Collecter la réponse complète
        full_response = ""
        try:
            for chunk in ollama_client.response(model, user_input, conversation, temp):
                if chunk:
                    full_response += chunk
                    print(chunk, end='', flush=True)  # Affichage temps réel
            
            print(f"\n\n📝 Réponse complète: {len(full_response)} caractères")
            
            # Générer et jouer l'audio
            tts_result = self.text_to_speech_and_play(
                text=full_response,
                voice=voice,
                speed=speed,
                auto_play=auto_play
            )
            
            # Combiner les résultats
            return {
                'text_response': full_response,
                'audio_file': tts_result.get('audio_file'),
                'tts_success': tts_result.get('success', False),
                'audio_played': tts_result.get('played', False),
                'error': tts_result.get('error')
            }
            
        except Exception as e:
            error_msg = f"Erreur lors du traitement Ollama+TTS: {e}"
            print(f"❌ {error_msg}")
            return {
                'text_response': full_response,
                'audio_file': None,
                'tts_success': False,
                'audio_played': False,
                'error': error_msg
            }