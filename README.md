# Jarvis — macOS AI Assistant

I wanted to make my own JARVIS-style assistant for my Mac, so I built one.

Jarvis lives in the macOS menu bar and lets me talk to it or type commands. The AI runs locally using Ollama, so I don't need a paid API or have to send my prompts to a cloud AI service.

## What it can do

*  Voice input using macOS speech tools
*  Text input from the menu bar
*  Cmd + Shift + J global hotkey
*  Local AI using Ollama + gemma:2b
*  Control system volume
*  Open and quit apps
*  Run basic system checks like uptime, disk space and ping
*  Quickly search the web
*  Run deeper research on a topic and save the results as a Markdown file
*  Generate essays and save them to a folder in Documents

## How it works

The main idea is pretty simple:

**You → Jarvis → Ollama → Gemma → Response**

Most of the processing happens locally on the Mac. Ollama handles the model, while Python handles the menu bar app, commands, hotkey and the rest of the logic.

## Running it

### 1. Set up the Python environment


uv venv
source .venv/bin/activate
uv pip install -r requirements.txt


### 2. Install and start Ollama


brew install ollama
ollama serve
ollama pull gemma:2b


### 3. Start Jarvis


python main.py


You should see the Jarvis icon appear in the macOS menu bar.

## Intel & Apple Silicon

The Python version works on both Intel Macs and Apple Silicon Macs (M1–M4).

The pre-built version in `dist/Jarvis` and the bundled flac-mac speech-to-text helper are currently x86_64, so Apple Silicon Macs need Rosetta for the compiled version.

If needed:

```bash
softwareupdate --install-rosetta
```

Running main.py directly is recommended if you're on Apple Silicon.

## macOS permissions

The first time you run Jarvis, macOS should ask for:

* **Accessibility** — needed for the global Cmd + Shift + J hotkey
* **Microphone** — needed for voice input

## Files

Research and essay output is saved here:

~/Documents/Jarvis_Research/


## Why I made it

I didn't want another assistant that needed an API key for everything. I wanted something small that could actually interact with my Mac while keeping the AI part local.

There's still a lot I want to improve, but this is a good starting point for my own little JARVIS.
