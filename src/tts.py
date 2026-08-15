import subprocess
import threading
import re
import logging
from config import TTS_VOICE, TTS_RATE

logger = logging.getLogger("jarvis.tts")

class TextToSpeech:
    """Native macOS Text-To-Speech wrapper using /usr/bin/say."""
    
    def __init__(self, voice: str = TTS_VOICE, rate: int = TTS_RATE):
        self.voice = voice
        self.rate = rate
        self._process = None
        self._lock = threading.Lock()

    def speak(self, text: str, async_mode: bool = True):
        """Convert text to speech using macOS native 'say' command."""
        clean_text = self._clean_text_for_speech(text)
        if not clean_text:
            return

        with self._lock:
            self.stop()  # Stop any ongoing speech first

            cmd = ["say", "-v", self.voice, "-r", str(self.rate), clean_text]
            
            try:
                if async_mode:
                    self._process = subprocess.Popen(cmd)
                else:
                    subprocess.run(cmd, check=True)
            except Exception as e:
                logger.error(f"Error executing TTS 'say': {e}")

    def stop(self):
        """Stop current speech output if active."""
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
            except Exception:
                pass
            self._process = None

    def _clean_text_for_speech(self, text: str) -> str:
        """Remove markdown syntax, URLs, and code blocks for natural vocal reading."""
        if not text:
            return ""
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', 'code block omitted.', text)
        # Remove inline backticks
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove markdown headers and emphasis
        text = re.sub(r'[\#\*\_\~\>]', '', text)
        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove raw URLs
        text = re.sub(r'https?://\S+', 'link omitted', text)
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

# Global singleton instance
tts = TextToSpeech()
