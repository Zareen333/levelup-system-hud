"""Asynchronous Text-to-Speech (TTS) System Voice engine using pyttsx3."""

import logging
import queue
import threading
from typing import Optional

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SystemVoice")


class SystemVoice:
    """Thread-safe asynchronous speech engine that wraps pyttsx3."""

    def __init__(self, rate: int = 160, volume: float = 1.0) -> None:
        """Initialize the SystemVoice manager.

        Args:
            rate: Target speech rate in words per minute (default ~160).
            volume: Speech output volume from 0.0 to 1.0.
        """
        self.rate: int = rate
        self.volume: float = volume
        self._queue: queue.Queue[Optional[str]] = queue.Queue()
        self._stop_event: threading.Event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        if pyttsx3 is not None:
            self._worker_thread = threading.Thread(
                target=self._speech_worker, daemon=True
            )
            self._worker_thread.start()
        else:
            logger.warning("pyttsx3 is not installed. Voice synthesis will be disabled.")

    def _speech_worker(self) -> None:
        """Worker thread function that initializes pyttsx3 and processes speech requests."""
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)

            # Attempt to set a deeper/male or robotic voice if available
            try:
                voices = engine.getProperty("voices")
                selected_voice = None
                for voice in voices:
                    name_lower = voice.name.lower()
                    if "david" in name_lower or "male" in name_lower or "george" in name_lower:
                        selected_voice = voice.id
                        break

                if selected_voice is None and voices:
                    selected_voice = voices[0].id

                if selected_voice:
                    engine.setProperty("voice", selected_voice)
            except Exception as voice_err:
                logger.debug("Voice selection warning: %s", voice_err)

            while not self._stop_event.is_set():
                try:
                    text = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if text is None:
                    self._queue.task_done()
                    break

                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as speak_err:
                    logger.error("Error during TTS execution: %s", speak_err)
                finally:
                    self._queue.task_done()

        except Exception as init_err:
            logger.error("Failed to initialize TTS engine worker: %s", init_err)

    def speak_async(self, text: str) -> None:
        """Enqueue text to be spoken asynchronously without blocking the UI.

        Args:
            text: Speech string to synthesize.
        """
        if not text or self._stop_event.is_set():
            return
        if self._worker_thread is None or not self._worker_thread.is_alive():
            logger.info("[System Voice (Fallback Mute)]: %s", text)
            return

        self._queue.put(text)

    def stop(self) -> None:
        """Clean up resources and stop the background TTS thread."""
        self._stop_event.set()
        self._queue.put(None)
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
