# Jarvis — Personal AI Assistant for macOS

A lightweight, hardware-optimized personal assistant designed for Mac computers (including low-spec Intel MacBook Air devices with 8GB RAM). 

Jarvis features a **Local-First Architecture**:
- **Local Brain**: Uses small quantized models (e.g. `gemma:2b` or `gemma3:1b`) via [Ollama](https://ollama.com) for zero-cost, privacy-preserving casual chat, command parsing, and local mac automation without hitting API rate limits.
- **Zero Electron Overhead**: Built as a native Python `rumps` menu bar application with under ~50MB idle RAM footprint.
- **Native macOS Audio**: Native Swift dictation tool (`SFSpeechRecognizer`) for lightweight STT and native `/usr/bin/say` for zero-overhead speech output.

---

## Features & Capabilities

1. **Global Hotkey Trigger**: Press `Cmd+Shift+J` anytime to activate voice dictation.
2. **Native Speech-to-Text (STT)**: Fast, low-memory dictation powered by compiled native Swift binary leveraging macOS Speech Framework.
3. **Native Text-to-Speech (TTS)**: Clean voice responses using macOS built-in `/usr/bin/say`.
4. **Direct Browser Search Commands**: Saying `"search [query]"` or `"google [query]"` immediately opens your default browser to Google Search results for the query while speaking confirmation.
5. **Local Mac Automation**:
   - Open/Quit Applications (e.g., `"open Safari"`, `"open Notes"`)
   - Volume Control (e.g., `"set volume to 50%"`, `"mute"`)
   - File Search & Content Reader (searches `Documents`, `Desktop`, `Downloads`)
   - Diagnostic System Info (`"date"`, `"uptime"`, `"sw_vers"`, etc.)
6. **Persistent Session Memory**: Rolling conversation history stored in SQLite (`~/.jarvis/memory.db`).

---

## Project Structure

```
jarvis v1/
├── config.py                 # System configuration & safety parameters
├── main.py                   # Main entry point for menu bar app
├── requirements.txt          # Python dependencies
├── native/
│   └── stt_helper.swift      # Swift source for macOS native speech recognizer tool
├── src/
│   ├── app.py                # rumps Menu Bar App UI & lifecycle manager
│   ├── brain.py               # AI Router (Ollama Gemma)
│   ├── listener.py           # Speech recognition wrapper for native binary
│   ├── tts.py                # macOS native 'say' TTS wrapper
│   ├── memory.py              # SQLite conversation context database
│   ├── tools/                 # Automation tools & allowlist security
│   │   ├── security.py
│   │   ├── system.py
│   │   ├── browser.py
│   │   ├── filesystem.py
│   │   └── registry.py
│   └── utils/
│       └── hotkey.py          # Global hotkey trigger listener (pynput)
└── tests/
    ├── test_tools.py          # Security & tool unit tests
    └── test_brain.py          # Router & memory unit tests
```

---

## Getting Started

### 1. Installation

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 2. Setting Up Ollama (Local Brain)

Install Ollama from [ollama.com](https://ollama.com) or Homebrew:

```bash
brew install ollama
```

Start the Ollama server and pull the small quantized Gemma model:

```bash
ollama serve
ollama pull gemma:2b
```

*(Note: On 8GB RAM Macs, `gemma:2b` or `gemma3:1b` fits comfortably within memory).*

---

## Running Jarvis

Launch the menu bar assistant:

```bash
python main.py
```

Look for the **Jarvis** icon in your macOS menu bar!

- Press **Cmd+Shift+J** or click **Listen** to speak.
- Or click **Type Request...** to enter commands manually.

---

## Verification & Testing

To run the automated unit test suite:

```bash
python -m unittest discover tests
```
