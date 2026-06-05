"""
Text-to-speech for the Hinton Digital Twin.
Uses pyttsx3 — works on Windows with no extra system installs (SAPI5).

Fix: pyttsx3 on Windows breaks if you call runAndWait() more than once on the
same engine instance. We work around this by creating a fresh engine for every
utterance inside its own thread.
"""

import threading
import re


def _strip_markdown(text: str) -> str:
    """Remove markdown so the TTS reads clean prose, not asterisks and hashes."""
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)   # bold / italic
    text = re.sub(r'#{1,6}\s*', '', text)                  # headings
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)         # code spans/blocks
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links → link text
    text = re.sub(r'[-*]\s+', '', text)                    # list bullets
    text = re.sub(r'\n{2,}', '. ', text)                   # paragraph breaks
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _check_pyttsx3_available() -> bool:
    try:
        import pyttsx3
        e = pyttsx3.init()
        e.stop()
        return True
    except Exception:
        return False


class HintonTTS:
    """
    Thin wrapper around pyttsx3.
    Each utterance gets its own fresh engine instance + its own thread.
    This is the only reliable way to reuse pyttsx3 on Windows (SAPI5).
    """

    def __init__(self, rate: int = 155, volume: float = 1.0):
        self._rate = rate
        self._volume = volume
        self._available = _check_pyttsx3_available()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()

    # ------------------------------------------------------------------
    def speak(self, text: str, block: bool = False) -> None:
        if not self._available:
            return

        clean = _strip_markdown(text)
        if not clean:
            return

        # Cancel any in-progress utterance
        self.stop()

        self._stop_flag.clear()

        if block:
            self._speak_sync(clean, self._stop_flag)
        else:
            t = threading.Thread(
                target=self._speak_sync,
                args=(clean, self._stop_flag),
                daemon=True
            )
            with self._lock:
                self._thread = t
            t.start()

    def stop(self) -> None:
        """Signal the current utterance to stop and wait for its thread to exit."""
        self._stop_flag.set()
        with self._lock:
            t = self._thread
            self._thread = None
        if t and t.is_alive():
            t.join(timeout=2)

    def wait(self) -> None:
        with self._lock:
            t = self._thread
        if t and t.is_alive():
            t.join()

    # ------------------------------------------------------------------
    def _speak_sync(self, text: str, stop_flag: threading.Event) -> None:
        """
        Create a brand-new pyttsx3 engine, speak, then destroy it.
        Running this in its own thread means the main loop is never blocked,
        and the engine never gets reused (which breaks SAPI5 on Windows).
        """
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)

            if stop_flag.is_set():
                return

            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception:
            pass   # Never crash the chat loop over TTS failures
