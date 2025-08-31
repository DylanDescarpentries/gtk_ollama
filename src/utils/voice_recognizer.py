import whisper
import sounddevice as sd
import numpy as np
import tempfile
import wave
import os
import time
import threading
from gi.repository import GLib


class VoiceRecognizer:
    def __init__(self, modele="small", sample_rate=16000, silence_threshold=0.01, silence_duree=2.0):
        """
        Classe pour la reconnaissance vocale optimisée FR avec arrêt automatique sur silence.

        Args:
            modele (str): Modèle Whisper à utiliser ("tiny", "base", "small", "medium", "large").
            sample_rate (int): Fréquence d'échantillonnage du micro.
            silence_threshold (float): Niveau d'énergie en dessous duquel on considère qu'il y a silence.
            silence_duree (float): Durée en secondes de silence avant d'arrêter l'enregistrement.
        """
        print(f"🔄 Chargement du modèle Whisper '{modele}'...")
        self.model = whisper.load_model(modele)
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_duree = silence_duree
        self.is_recording = False
        self.stop_recording = False

    def _enregistrer_audio_callback(self):
        """Version avec callback pour éviter les problèmes de threading."""
        audio_total = []
        silence_start = None
        self.is_recording = True
        self.stop_recording = False
        
        duree_chunk = 0.5  # Réduit pour une meilleure réactivité
        
        print("🎤 Parlez... (l'écoute s'arrête quand vous êtes silencieux)")
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Statut audio: {status}")
            
            # Calcul de l'énergie du signal
            energie = np.sqrt(np.mean(indata**2))
            
            # Stockage des données audio
            audio_total.append(indata.copy().flatten())
            
            # Gestion du silence dans le callback
            nonlocal silence_start
            if energie < self.silence_threshold:
                if silence_start is None:
                    silence_start = time.inputBufferAdcTime
                elif (time.inputBufferAdcTime - silence_start) > self.silence_duree:
                    self.stop_recording = True
            else:
                silence_start = None

        # Configuration du stream audio
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            callback=audio_callback,
            blocksize=int(duree_chunk * self.sample_rate)
        ):
            # Boucle d'attente jusqu'à l'arrêt
            while not self.stop_recording:
                time.sleep(0.1)
        
        self.is_recording = False
        
        if audio_total:
            return np.concatenate(audio_total, axis=0)
        else:
            return np.array([])

    def _enregistrer_audio_bloquant(self):
        """Version bloquante améliorée avec gestion d'erreurs."""
        duree_chunk = 0.3
        audio_total = []
        silence_start = None
        temps_total = 0
        max_duree = 30  # Limite de sécurité à 30 secondes

        
        try:
            while temps_total < max_duree:
                # Enregistrement synchrone d'un chunk
                chunk = sd.rec(
                    int(duree_chunk * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype=np.float32,
                    blocking=True  # Bloquant pour éviter les problèmes de thread
                )
                
                audio_total.append(chunk.flatten())
                temps_total += duree_chunk

                # Calcul de l'énergie RMS (plus robuste)
                energie_rms = np.sqrt(np.mean(chunk**2))
                
                # detecte les silences et coupe l'enregistrement
                if energie_rms < self.silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                        #stop l'enregistrement à la fin du décompte
                    elif time.time() - silence_start > self.silence_duree:
                        break
                else:
                    if silence_start is not None:
                        print("🔊 Reprise de la parole détectée.")
                    silence_start = None
                    
        except Exception as e:
            print(f"Erreur lors de l'enregistrement: {e}")
            
        return np.concatenate(audio_total, axis=0) if audio_total else np.array([])

    def transcrire_micro(self):
        """Enregistre au micro puis transcrit en français."""
        # Utilisation de la version bloquante qui fonctionne mieux dans les threads
        audio_array = self._enregistrer_audio_bloquant()
        
        if len(audio_array) == 0:
            return "Aucun audio enregistré."

        # Sauvegarde temporaire
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                with wave.open(tmp_file.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    # Normalisation pour éviter la saturation
                    audio_normalized = np.clip(audio_array, -1.0, 1.0)
                    wf.writeframes((audio_normalized * 32767).astype(np.int16).tobytes())

                # Transcription Whisper
                result = self.model.transcribe(
                    tmp_file.name,
                    language="fr",
                    task="transcribe",
                    fp16=False,
                    temperature=0.0,
                    initial_prompt="Ceci est une transcription en français avec ponctuation naturelle."
                )

                os.unlink(tmp_file.name)
                return result["text"].strip()
                
        except Exception as e:
            print(f"Erreur lors de la transcription: {e}")
            return f"Erreur: {e}"

    def transcrire_micro_async(self, callback):
        """Version asynchrone pour GTK avec callback."""
        def worker():
            try:
                texte = self.transcrire_micro()
                # Utiliser GLib.idle_add pour retourner dans le thread principal
                GLib.idle_add(callback, texte)
            except Exception as e:
                GLib.idle_add(callback, f"Erreur: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    def transcrire_fichier(self, chemin_fichier):
        """Transcrit un fichier audio existant."""
        try:
            result = self.model.transcribe(
                chemin_fichier,
                language="fr",
                task="transcribe",
                fp16=False,
                temperature=0.0,
                initial_prompt="Ceci est une transcription en français avec ponctuation naturelle."
            )
            return result["text"].strip()
        except Exception as e:
            return f"Erreur lors de la transcription du fichier: {e}"