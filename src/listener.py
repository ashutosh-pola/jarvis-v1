import io
import os
import wave
import time
import logging
import numpy as np
from typing import Tuple

logger = logging.getLogger("jarvis.listener")

try:
    import sounddevice as sd
    import speech_recognition as sr
    HAS_PYTHON_STT = True
except ImportError:
    HAS_PYTHON_STT = False

from config import STT_BINARY_PATH

class SpeechListener:
    """Microphone recording and Speech-To-Text listener for Jarvis."""

    def __init__(self):
        self.recognizer = sr.Recognizer() if HAS_PYTHON_STT else None

    def is_available(self) -> bool:
        """Check if STT is supported."""
        return HAS_PYTHON_STT or os.path.exists(STT_BINARY_PATH)

    def listen(self, max_seconds: float = 7.0, silence_timeout: float = 1.5) -> Tuple[bool, str]:
        """
        Record microphone audio and transcribe to text.
        Returns tuple: (success_flag, transcribed_text_or_error_msg)
        """
        if HAS_PYTHON_STT:
            return self._listen_python_sounddevice(max_seconds=max_seconds, silence_timeout=silence_timeout)
        else:
            return self._listen_native_binary(max_seconds=max_seconds, silence_timeout=silence_timeout)

    def _listen_python_sounddevice(self, max_seconds: float = 7.0, silence_timeout: float = 1.5) -> Tuple[bool, str]:
        """Record audio via sounddevice with silence detection and transcribe via SpeechRecognition."""
        sample_rate = 16000
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(sample_rate * chunk_duration)
        
        audio_chunks = []
        silence_start = None
        start_time = time.time()
        speech_detected = False

        logger.info("Listening for voice input...")

        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
                while True:
                    data, overflow = stream.read(chunk_samples)
                    if overflow:
                        logger.debug("Audio buffer overflow")

                    audio_chunks.append(data)
                    chunk_arr = np.frombuffer(data, dtype=np.int16)
                    rms = np.sqrt(np.mean(chunk_arr.astype(np.float32) ** 2))

                    # Speech detection threshold
                    if rms > 300:
                        speech_detected = True
                        silence_start = None
                    elif speech_detected:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= silence_timeout:
                            logger.info("Silence detected. Stopping recording.")
                            break

                    # Hard timeout
                    if time.time() - start_time >= max_seconds:
                        logger.info("Max recording duration reached.")
                        break

            if not audio_chunks:
                return False, "No audio recorded"

            recorded_bytes = np.concatenate(audio_chunks, axis=0).tobytes()

            # Create WAV in memory
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recorded_bytes)
            wav_io.seek(0)

            # Recognize speech
            with sr.AudioFile(wav_io) as source:
                audio_data = self.recognizer.record(source)

            transcribed = self.recognizer.recognize_google(audio_data)
            if transcribed and transcribed.strip():
                logger.info(f"Transcribed: {transcribed}")
                return True, transcribed.strip()
            else:
                return False, "No speech recognized"

        except sr.UnknownValueError:
            return False, "No speech recognized"
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return False, f"Speech API Error: {e}"
        except Exception as e:
            logger.error(f"Audio recording exception: {e}")
            return False, str(e)

    def _listen_native_binary(self, max_seconds: float = 7.0, silence_timeout: float = 1.5) -> Tuple[bool, str]:
        """Fallback to compiled binary if sounddevice is absent."""
        import subprocess, json
        if not os.path.exists(STT_BINARY_PATH):
            return False, "STT engine unavailable"

        try:
            cmd = [str(STT_BINARY_PATH), str(max_seconds), str(silence_timeout)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=max_seconds + 5.0)

            stdout_text = result.stdout.strip()
            if not stdout_text:
                return False, "No speech recognized"

            data = json.loads(stdout_text)
            status = data.get("status", "")
            text = data.get("text", "")

            if status == "success" and text:
                return True, text
            return False, "No speech recognized"
        except Exception as e:
            return False, str(e)

# Global listener instance
listener = SpeechListener()
