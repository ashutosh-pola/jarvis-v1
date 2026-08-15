import sys
import os
import logging

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.listener import listener
from src.app import JarvisApp

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    setup_logging()
    logger = logging.getLogger("jarvis.main")
    logger.info("Initializing Jarvis Personal AI Assistant for macOS...")

    # Ensure native STT tool is built
    if not listener.is_available():
        logger.info("Native STT helper tool not compiled. Compiling stt_helper.swift...")
        listener.compile_stt_helper()

    app = JarvisApp()
    app.start_hotkey_listener()
    logger.info("Jarvis running in menu bar. Press Cmd+Shift+J or click menu icon to interact.")
    app.run()

if __name__ == "__main__":
    main()
