# Jarvis

> **Apple Silicon (M-chip) Note**: Running from source (`python main.py`) works natively on both Apple Silicon (M1–M4) and Intel Macs.

A lightweight, local-first AI assistant in your macOS menu bar. Powered by Ollama (`gemma:2b`) and native macOS speech tools. Everything runs on-device — no cloud API, no accounts, no data leaving your Mac.

## Platform support

**Packaged app (`dist/Jarvis`): Intel Macs only (`x86_64`).**

The compiled executable and the bundled STT helper (`flac-mac`, shipped inside the `speech_recognition` library) are both `x86_64`-only. On Apple Silicon (M1/M2/M3/M4) this will fail to launch with a `bad CPU type in executable` error.

**If you're on Apple Silicon, you have two options:**

1. **Enable Rosetta** and run the packaged app as-is:
   ```bash
   softwareupdate --install-rosetta
   ```
   Once installed, `dist/Jarvis` runs fine under emulation — no other changes needed.

2. **Run from source instead** (recommended — no Rosetta needed, native performance):
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   python main.py
   ```

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

### 1. Install dependencies
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Install & start Ollama
```bash
brew install ollama
ollama serve
ollama pull gemma:2b
```

### 3. Run Jarvis

```bash
python main.py
```

Look for the **Jarvis** icon in your menu bar.

### 4. First-launch permissions

macOS will likely prompt for two permissions the first time you use certain features:
- **Accessibility** — needed for the global hotkey (`Cmd+Shift+J`) to register system-wide. Grant it under System Settings → Privacy & Security → Accessibility.
- **Microphone** — needed for voice input (Listen).

If you're running the packaged binary (not from source) and macOS refuses to open it at all, clear the quarantine flag first:
```bash
xattr -dr com.apple.quarantine Jarvis
```

---

## Usage

- **Hotkey**: Press `Cmd + Shift + J` to start voice dictation.
- **Menu Bar**: Click the icon to **Listen**, **Type Request**, check **Ollama Status**, or **Clear Conversation History**.

---

## Features

- **Voice commands** — control volume, open/quit apps, run diagnostic commands
- **Deep research** — say "deep research [topic]" to generate a Markdown report saved to `~/Documents/Jarvis_Research/`
- **Browser search** — say "search [query]" to open search results instantly
- **Local & private** — runs entirely on your Mac, zero API costs, nothing leaves the device

---

## Building the executable yourself

If you want to rebuild `dist/Jarvis` after making changes:

```bash
rm -rf build dist
python3 -m PyInstaller --noconfirm Jarvis.spec
```

Wait for it to finish (watch for `Building EXE from EXE-00.toc completed successfully.`), then verify:
```bash
file dist/Jarvis
```
Should report `Mach-O 64-bit x86_64 executable` (this build is Intel-only — see Platform Support above).

---

## Known limitations

- Apple Silicon Macs need Rosetta or must run from source (see Platform Support)
- `run_shell_command` is restricted to a fixed allowlist of safe, read-only commands (`date`, `uptime`, `df`, `ls`, `ping`, etc.) — this is intentional, not a bug
- File access is sandboxed to `~/Documents`, `~/Desktop`, and `~/Downloads`
