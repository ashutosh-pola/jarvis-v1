import threading
import logging
from pynput import keyboard
from config import DEFAULT_HOTKEY

logger = logging.getLogger("jarvis.hotkey")

class GlobalHotkeyListener:
    """Global hotkey listener using pynput for background activation."""

    def __init__(self, hotkey_str: str = DEFAULT_HOTKEY, on_trigger=None):
        self.hotkey_str = hotkey_str
        self.on_trigger = on_trigger
        self.listener = None
        self._thread = None

    def start(self):
        """Start listening for the global hotkey in a background thread."""
        try:
            hotkey_map = {self.hotkey_str: self._handle_trigger}
            self.listener = keyboard.GlobalHotKeys(hotkey_map)
            self._thread = threading.Thread(target=self.listener.run, daemon=True)
            self._thread.start()
            logger.info(f"Global hotkey listener started for '{self.hotkey_str}'")
        except Exception as e:
            logger.error(f"Failed to start global hotkey listener: {e}")

    def stop(self):
        """Stop hotkey listener."""
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass

    def _handle_trigger(self):
        logger.info("Global hotkey triggered!")
        if self.on_trigger:
            self.on_trigger()
