# Jarvis — macOS AI Assistant

A lightweight, local-first AI assistant in your macOS menu bar. Powered by Ollama (`gemma:2b`) and native macOS speech tools.

---

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install & Start Ollama
```bash
brew install ollama
ollama serve
ollama pull gemma:2b
```

### 3. Run Jarvis
```bash
python main.py
```

Look for the **Jarvis** icon in your menu bar!

---

## Usage

- **Hotkey**: Press `Cmd + Shift + J` to start voice dictation.
- **Menu Bar**: Click the icon to **Listen**, **Type Request**, or access settings.

---

## Features

- **Voice Commands**: Control volume, open/quit apps, or run diagnostic commands.
- **Deep Research**: Say `"deep research [topic]"` to generate a Markdown report saved to `~/Documents/Jarvis_Research/`.
- **Browser Search**: Say `"search [query]"` to open search results instantly.
- **Local & Private**: Runs locally on your Mac with zero API costs.
