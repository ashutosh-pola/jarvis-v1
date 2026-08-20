import os
import re
import json
import logging
import urllib.request
from typing import Dict, Any, Tuple

from config import OLLAMA_HOST, LOCAL_MODEL
from src.memory import memory
from src.tools.registry import TOOL_SCHEMAS, execute_tool
from src.tools.os_tools import open_google_search

logger = logging.getLogger("jarvis.brain")

SYSTEM_PROMPT = """You are Jarvis, a helpful, witty, and intelligent personal AI assistant running on macOS.
Role & Instructions:
1. Be friendly, conversational, and direct.
2. Discuss TV shows, pop culture, fiction, hobbies, coding, and general knowledge freely.
3. You have access to local macOS tools and capabilities:
   - Volume control (set_volume, get_volume, mute).
   - Application controls (open_app, quit_app).
   - System diagnostics (uptime, disk space df, macOS sw_vers, network ping).
   - Deep research & essay generation (perform_deep_research saved to ~/Documents/Jarvis_Research/).
   - Web browser search (open_google_search).
   - File search and text file reading in user directories.
4. Keep responses concise, engaging, and clear for vocal speech synthesis. Do not use emojis in your responses.
5. When requested to perform actions, answer directly or execute tool calls cleanly.
"""

class BrainRouter:
    """AI Router: Local Gemma via Ollama."""

    def __init__(self, ollama_host: str = OLLAMA_HOST, local_model: str = LOCAL_MODEL):
        self.ollama_host = ollama_host.rstrip('/')
        self.local_model = local_model

    def check_ollama_status(self) -> Tuple[bool, str]:
        """Check if local Ollama server is running and model is present."""
        try:
            req = urllib.request.Request(f"{self.ollama_host}/api/tags")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    models = [m.get('name', '') for m in data.get('models', [])]
                    if any(self.local_model in m for m in models):
                        return True, f"Ollama online with model '{self.local_model}'"
                    return True, f"Ollama online, but model '{self.local_model}' not found in {models}"
        except Exception as e:
            return False, f"Ollama offline: {e}"
        return False, "Ollama unreachable"

    def process_query(self, user_input: str) -> str:
        """Route user query to browser action, deep research engine, or local Gemma brain."""
        prompt = user_input.strip()
        if not prompt:
            return "I didn't catch that. How can I help you?"

        # Save user message to memory
        memory.add_message("user", prompt)

        # 1. Intent Category: Deep Research & Essay Writing ("deep research [X]", "write an essay on [X]", "make a report on [X]")
        research_match = re.match(r'^(?:deep research|do deep research on|thoroughly research|deep dive into|research|make a research report on|make a report on|write a report on|write an essay on|essay on)\s+(.+)$', prompt, re.IGNORECASE)
        if research_match:
            topic = research_match.group(1).strip()
            res = execute_tool("perform_deep_research", {"topic": topic})
            reply = res.get("spoken_summary") or res.get("message")
            memory.add_message("assistant", reply)
            return reply

        # 2. Intent Category: Browser Search Command ("search [X]" / "google [X]")
        search_match = re.match(r'^(?:search|google|look up on google|search for)\s+(.+)$', prompt, re.IGNORECASE)
        if search_match:
            query = search_match.group(1).strip()
            res = open_google_search(query)
            reply = f"Opening Google search results for {query} in your default browser."
            memory.add_message("assistant", reply)
            return reply

        # 3. Intent Category: Local Gemma Brain
        reply = self._query_local_gemma(prompt)

        memory.add_message("assistant", reply)
        return reply

    def _query_local_gemma(self, prompt: str) -> str:
        """Send prompt to local Gemma model via Ollama API."""
        recent_turns = memory.get_recent_history()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + recent_turns

        # Check direct rule parsing for simple offline commands
        simple_action = self._check_fast_rule_action(prompt)
        if simple_action:
            return simple_action

        try:
            url = f"{self.ollama_host}/api/chat"
            payload = {
                "model": self.local_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 180
                }
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )

            # Allow up to 180 seconds for deep reasoning on CPU
            with urllib.request.urlopen(req, timeout=180.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    msg = data.get("message", {})
                    content = msg.get("content", "").strip()
                    
                    # Handle tool call if returned by model
                    tool_calls = msg.get("tool_calls", [])
                    if tool_calls:
                        res_list = []
                        for tool_call in tool_calls:
                            fn = tool_call.get("function", {})
                            fn_name = fn.get("name", "")
                            fn_args = fn.get("arguments", {})
                            tool_res = execute_tool(fn_name, fn_args)
                            msg_str = tool_res.get("message") or f"Executed tool {fn_name}"
                            res_list.append(msg_str)
                        return ". ".join(res_list)

                    if content:
                        return content
        except Exception as e:
            logger.warning(f"Ollama local brain query failed: {e}")

        # Fallback if Ollama is slow/offline
        return self._rule_based_fallback(prompt)

    def _check_single_fast_rule(self, prompt: str) -> str:
        """Match a single offline command phrase."""
        lower = prompt.lower().strip()

        # Volume controls
        vol_match = re.search(r'(?:set volume|volume)(?: to)? (\d+)', lower)
        if vol_match:
            level = int(vol_match.group(1))
            res = execute_tool("set_volume", {"level": level})
            return res.get("message", f"Volume set to {level}%")

        if any(kw in lower for kw in ["lower volume", "reduce volume", "decrease volume", "turn down volume", "volume down"]):
            vol_res = execute_tool("get_volume", {})
            current = vol_res.get("volume", 50)
            new_vol = max(0, current - 15)
            res = execute_tool("set_volume", {"level": new_vol})
            return res.get("message", f"System volume set to {new_vol}%")

        if any(kw in lower for kw in ["increase volume", "raise volume", "turn up volume", "volume up"]):
            vol_res = execute_tool("get_volume", {})
            current = vol_res.get("volume", 50)
            new_vol = min(100, current + 15)
            res = execute_tool("set_volume", {"level": new_vol})
            return res.get("message", f"System volume set to {new_vol}%")

        if lower in ["mute", "mute volume"]:
            res = execute_tool("set_volume", {"level": 0})
            return res.get("message", "Muted audio")

        # Open App commands
        open_match = re.search(r'^(?:open|launch|start)\s+([a-zA-Z0-9\s]+)$', lower)
        if open_match:
            app_name = open_match.group(1).strip()
            if app_name not in ["the browser", "google", "search"]:
                res = execute_tool("open_app", {"app_name": app_name})
                return res.get("message", f"Opening {app_name}")

        # Quit App commands
        quit_match = re.search(r'^(?:quit|close|stop)\s+([a-zA-Z0-9\s]+)$', lower)
        if quit_match:
            app_name = quit_match.group(1).strip()
            res = execute_tool("quit_app", {"app_name": app_name})
            return res.get("message", f"Quit {app_name}")

        return ""

    def _check_fast_rule_action(self, prompt: str) -> str:
        """Fast offline rule matcher for instant response to common mac commands, supporting multi-command chains."""
        # Check multi-step command connected by 'and', 'then', or ';'
        parts = re.split(r'\s+(?:and|then)\s+|;\s*', prompt, flags=re.IGNORECASE)
        if len(parts) > 1:
            results = []
            for part in parts:
                part_res = self._check_single_fast_rule(part)
                if part_res:
                    results.append(part_res)
            if len(results) == len(parts):
                return ". ".join(results)

        # Check single command
        return self._check_single_fast_rule(prompt)

    def _rule_based_fallback(self, prompt: str) -> str:
        """Graceful offline fallback response when local LLM server is starting or offline."""
        fast_res = self._check_fast_rule_action(prompt)
        if fast_res:
            return fast_res

        lower = prompt.lower()
        if "hello" in lower or "hi" in lower or "hey jarvis" in lower:
            return "Hello! Jarvis here. How can I assist you today?"
        elif "who are you" in lower:
            return "I am Jarvis, your personal macOS AI assistant."
        elif "time" in lower or "what time" in lower:
            res = execute_tool("run_shell_command", {"cmd": "date"})
            return f"Current time is: {res.get('output', '')}"

        return "I heard you, but my local reasoning model (Ollama Gemma) is taking longer than expected to respond. Please try asking again."

# Global brain router instance
brain = BrainRouter()
DualBrainRouter = BrainRouter  # Backwards compatibility alias
