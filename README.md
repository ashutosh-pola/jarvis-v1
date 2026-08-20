# Jarvis

> **Apple Silicon (M-chip) Note**: Running from source (`python main.py`) works natively on both Apple Silicon (M1–M4) and Intel Macs.

A simple macOS menu bar assistant built to handle basic voice controls, local LLM queries, and web research without sending data to external servers or paying for API keys.

Powered by **Ollama** (`gemma:2b`) and native macOS speech tools.

---

## Features

- **Voice dictation**: Hit `Cmd + Shift + J` anywhere to start talking.
- **System controls**: Change volume, open/quit apps, and check system diagnostics (`uptime`, `df`, `ping`).
- **Deep research & essays**: Say *"deep research [topic]"* or *"write an essay on [topic]"* to save a Markdown report to `~/Documents/Jarvis_Research/`.
- **Quick web search**: Say *"search [query]"* to open Google search results in your default browser.
- **100% offline**: All model inference and chat history stay local on your Mac.

---

## Getting Started

### 1. Dependencies

```bash
pip install -r requirements.txt
```

### 2. Ollama

```bash
brew install ollama
ollama serve
ollama pull gemma:2b
```

### 3. Run Jarvis

```bash
python main.py
```

*Grant Accessibility (global hotkey) and Microphone permissions when prompted on first run.*
