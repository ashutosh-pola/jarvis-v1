import threading
import logging
import rumps
from typing import Optional
from PyObjCTools import AppHelper

from config import DEFAULT_HOTKEY, LOCAL_MODEL
from src.listener import listener
from src.brain import brain
from src.tts import tts
from src.memory import memory
from src.utils.hotkey import GlobalHotkeyListener

logger = logging.getLogger("jarvis.app")

class JarvisApp(rumps.App):
    """Lightweight macOS Menu Bar Application for Jarvis Assistant."""

    def __init__(self):
        super(JarvisApp, self).__init__("Jarvis", quit_button=None)
        
        # Define menu items
        self.listen_item = rumps.MenuItem("Listen (Cmd+Shift+J)", callback=self.on_listen_clicked)
        self.text_item = rumps.MenuItem("Type Request...", callback=self.on_type_request_clicked)
        self.status_item = rumps.MenuItem("Ollama Status", callback=self.on_check_status_clicked)
        self.clear_item = rumps.MenuItem("Clear Conversation History", callback=self.on_clear_history_clicked)
        self.quit_item = rumps.MenuItem("Quit Jarvis", callback=self.on_quit_clicked)

        self.menu = [
            self.listen_item,
            self.text_item,
            None,  # Separator
            self.status_item,
            self.clear_item,
            None,  # Separator
            self.quit_item
        ]

        self.is_processing = False
        self.hotkey_listener: Optional[GlobalHotkeyListener] = None

    def start_hotkey_listener(self):
        """Initialize global hotkey trigger."""
        self.hotkey_listener = GlobalHotkeyListener(DEFAULT_HOTKEY, on_trigger=self.trigger_listening)
        self.hotkey_listener.start()

    def set_status(self, text: str):
        """Update menu bar title indicator."""
        self.title = f"Jarvis {text}".strip()

    @rumps.clicked("Listen (Cmd+Shift+J)")
    def on_listen_clicked(self, _):
        self.trigger_listening()

    def trigger_listening(self):
        """Trigger voice input flow in a background thread."""
        if self.is_processing:
            return
        
        self.is_processing = True
        threading.Thread(target=self._listen_and_respond_flow, daemon=True).start()

    def _listen_and_respond_flow(self):
        """Execute STT -> Brain Router -> TTS pipeline."""
        try:
            AppHelper.callAfter(self.set_status, "[Listening...]")
            tts.speak("Listening...", async_mode=True)
            
            # Step 1: Capture speech using native STT helper
            success, text_or_err = listener.listen(max_seconds=10.0, silence_timeout=1.8)
            
            if not success:
                logger.info(f"Speech capture result: {text_or_err}")
                AppHelper.callAfter(self.set_status, "")
                if "No speech recognized" not in text_or_err:
                    tts.speak(f"Sorry, {text_or_err}")
                self.is_processing = False
                return

            # Step 2: Query Brain Router
            self._process_text_request(text_or_err)

        except Exception as e:
            logger.error(f"Error in listen and respond flow: {e}")
            AppHelper.callAfter(self.set_status, "")
            self.is_processing = False

    @rumps.clicked("Type Request...")
    def on_type_request_clicked(self, _):
        """Open text input prompt modal."""
        window = rumps.Window("Enter your command or question for Jarvis:", "Type Request", cancel=True, dimensions=(320, 80))
        response = window.run()
        if response.clicked and response.text.strip():
            user_text = response.text.strip()
            threading.Thread(target=self._process_text_request, args=(user_text,), daemon=True).start()

    def _process_text_request(self, user_text: str):
        """Send prompt to brain and speak/display response."""
        self.is_processing = True
        try:
            AppHelper.callAfter(self.set_status, "[Thinking...]")
            logger.info(f"User Request: {user_text}")

            # Get brain response
            reply = brain.process_query(user_text)
            logger.info(f"Jarvis Response: {reply}")

            AppHelper.callAfter(self.set_status, "[Speaking...]")
            tts.speak(reply, async_mode=False)

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            tts.speak("An error occurred processing your request.")
        finally:
            AppHelper.callAfter(self.set_status, "")
            self.is_processing = False

    def _do_check_status(self):
        """Perform status check in background thread and show alert on main thread."""
        online, msg = brain.check_ollama_status()
        if online:
            alert_msg = f"{msg}"
        else:
            alert_msg = f"{msg}\n\nTo start Ollama, run 'ollama serve' in Terminal and pull {LOCAL_MODEL}."
        AppHelper.callAfter(rumps.alert, title="Ollama Status", message=alert_msg)

    @rumps.clicked("Ollama Status")
    def on_check_status_clicked(self, _):
        """Check Ollama local server connectivity in background thread."""
        threading.Thread(target=self._do_check_status, daemon=True).start()

    @rumps.clicked("Clear Conversation History")
    def on_clear_history_clicked(self, _):
        memory.clear_history()
        rumps.notification("Jarvis Memory", "Conversation History Cleared", "Memory database reset.")

    def on_quit_clicked(self, _):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        rumps.quit_application()
        
