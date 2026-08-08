"""Background Voice Command Listener engine with native sample rate mic capture and robust intent recognition."""

import io
import logging
import queue
import re
import threading
import wave
from typing import Any, Optional, Tuple

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    sd = None
    np = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceListener")


class VoiceListener:
    """Continuous background microphone listener for recognizing spoken System commands."""

    def __init__(self) -> None:
        """Initialize background listener thread and command queue."""
        self._command_queue: queue.Queue[Tuple[str, Any]] = queue.Queue()
        self._stop_event: threading.Event = threading.Event()
        self._is_active: bool = False
        self._status_msg: str = "INITIALIZING"
        self._last_heard: str = ""
        self._worker_thread: Optional[threading.Thread] = None

        if sr is not None:
            self._worker_thread = threading.Thread(
                target=self._listen_worker, daemon=True
            )
            self._worker_thread.start()
        else:
            self._status_msg = "SR LIB NOT INSTALLED"
            logger.warning("speech_recognition package not installed. Voice listener disabled.")

    @property
    def is_active(self) -> bool:
        """Return True if background listener is running and mic is capturing."""
        return self._is_active

    @property
    def status_message(self) -> str:
        """Return current user-friendly microphone status string."""
        return self._status_msg

    @property
    def last_heard(self) -> str:
        """Return the last recognized spoken phrase."""
        return self._last_heard

    def get_command(self) -> Optional[Tuple[str, Any]]:
        """Non-blocking pop of the next recognized command tuple from queue."""
        try:
            return self._command_queue.get_nowait()
        except queue.Empty:
            return None

    def _listen_worker(self) -> None:
        """Background thread loop capturing microphone audio and recognizing spoken intent."""
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 200
        recognizer.pause_threshold = 0.8

        mic = None
        use_sounddevice = False
        native_samplerate = 44100
        channels = 1

        # Attempt 1: Standard PyAudio microphone
        try:
            mic = sr.Microphone()
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self._is_active = True
            self._status_msg = "LISTENING 🎤"
            logger.info("Voice Command Listener activated via PyAudio.")
        except Exception:
            # Attempt 2: sounddevice fallback with native mic sample rate detection
            if sd is not None and np is not None:
                try:
                    info = sd.query_devices(kind='input')
                    if info:
                        native_samplerate = int(info.get('default_samplerate', 44100))
                        channels = min(int(info.get('max_input_channels', 1)), 2)
                        if channels <= 0:
                            channels = 1
                        use_sounddevice = True
                        self._is_active = True
                        self._status_msg = "LISTENING 🎤"
                        logger.info(
                            "Voice Command Listener activated via sounddevice (Device: %s, Rate: %d Hz, Channels: %d).",
                            info.get('name', 'Default'),
                            native_samplerate,
                            channels,
                        )
                except Exception as sd_err:
                    logger.warning("sounddevice input query failed: %s", sd_err)

        if not self._is_active:
            self._status_msg = "NO MIC CONNECTED"
            logger.warning("No working microphone device or audio driver found. Voice commands disabled.")
            return

        chunk_duration = 3.0  # seconds

        while not self._stop_event.is_set():
            try:
                audio = None

                if not use_sounddevice and mic is not None:
                    with mic as source:
                        audio = recognizer.listen(source, timeout=2.0, phrase_time_limit=4.0)

                elif use_sounddevice and sd is not None and np is not None:
                    num_samples = int(native_samplerate * chunk_duration)
                    recording = sd.rec(
                        num_samples, samplerate=native_samplerate, channels=channels, dtype='int16'
                    )
                    sd.wait()

                    # Convert multi-channel to mono if stereo
                    if channels > 1:
                        mono_data = np.mean(recording, axis=1).astype(np.int16)
                    else:
                        mono_data = recording.flatten()

                    max_amplitude = np.max(np.abs(mono_data))

                    # Process audio if sound energy crosses threshold
                    if max_amplitude > 200:
                        wav_buf = io.BytesIO()
                        with wave.open(wav_buf, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)  # 16-bit PCM
                            wf.setframerate(native_samplerate)
                            wf.writeframes(mono_data.tobytes())

                        audio = sr.AudioData(wav_buf.getvalue(), native_samplerate, 2)

                if audio is not None:
                    self._status_msg = "PROCESSING 🧠"
                    text = recognizer.recognize_google(audio).strip()
                    self._last_heard = text
                    self._status_msg = f'HEARD "{text.upper()}"'
                    logger.info("Voice Listener recognized phrase: '%s'", text)

                    command = self.parse_intent(text)
                    if command:
                        self._command_queue.put(command)
                        logger.info("Executed voice command intent: %s", command)
                    else:
                        logger.info("Unrecognized spoken intent phrase: '%s'", text)

                else:
                    self._status_msg = "LISTENING 🎤"

            except sr.WaitTimeoutError:
                self._status_msg = "LISTENING 🎤"
                continue
            except sr.UnknownValueError:
                self._status_msg = "LISTENING 🎤"
                continue
            except sr.RequestError as req_err:
                self._status_msg = "NETWORK SR ERROR"
                logger.warning("Speech recognition request failed: %s", req_err)
            except Exception as err:
                logger.debug("Voice listening loop iteration error: %s", err)
                self._status_msg = "LISTENING 🎤"

    def parse_intent(self, phrase: str) -> Optional[Tuple[str, Any]]:
        """Parse raw speech text into a structured command tuple.

        Args:
            phrase: Raw transcribed text string.

        Returns:
            Tuple of (command_name, arg) or None if unhandled phrase.
        """
        clean = phrase.lower().strip()

        # Command: Add Quest by Voice (e.g., "add quest run 5 kilometers", "new quest study physics")
        if clean.startswith("add quest ") or clean.startswith("new quest ") or clean.startswith("create quest "):
            title_text = clean.replace("add quest ", "").replace("new quest ", "").replace("create quest ", "").strip().title()
            if title_text:
                return ("addquest", {"title": title_text, "xp": 50, "category": "General"})

        # Command: Level Up
        if "level" in clean or "upgrade" in clean:
            return ("levelup", None)

        # Command: View Mode Toggle
        if "mobile" in clean or "desktop" in clean or "switch" in clean or "toggle" in clean:
            return ("toggle_mode", None)

        # Map numbers, words, and ordinals
        num_map = {
            "one": 1, "1": 1, "1st": 1, "first": 1,
            "two": 2, "2": 2, "2nd": 2, "second": 2,
            "three": 3, "3": 3, "3rd": 3, "third": 3,
            "four": 4, "4": 4, "4th": 4, "fourth": 4,
            "five": 5, "5": 5, "5th": 5, "fifth": 5,
            "six": 6, "6": 6, "6th": 6, "sixth": 6,
            "seven": 7, "7": 7, "7th": 7, "seventh": 7,
            "eight": 8, "8": 8, "8th": 8, "eighth": 8,
            "nine": 9, "9": 9, "9th": 9, "ninth": 9
        }

        # Check explicit quest numbers or direct numbers (e.g. "complete quest 1", "done 2", "quest one")
        for word, idx in num_map.items():
            if re.search(rf"\b(complete|finish|do|done|quest)?\s*{word}\b", clean):
                return ("complete_index", idx - 1)

        # Check quest title / category keywords (e.g. "pushups", "push ups", "python", "study", "code", "coding", "run")
        keywords = ["pushup", "push-up", "push up", "python", "study", "code", "coding", "run", "read", "physical", "intellect"]
        for kw in keywords:
            if kw in clean:
                return ("complete_keyword", kw)

        # Fallback: if phrase starts with "complete" or "finish", pass remainder as keyword
        if clean.startswith("complete ") or clean.startswith("finish ") or clean.startswith("do "):
            kw = clean.replace("complete ", "").replace("finish ", "").replace("do ", "").strip()
            if kw:
                return ("complete_keyword", kw)

        return None

    def stop(self) -> None:
        """Stop background listening worker thread."""
        self._stop_event.set()
        self._is_active = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
