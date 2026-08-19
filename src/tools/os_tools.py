import os
import subprocess
import urllib.parse
import logging
from pathlib import Path
from typing import Dict, Any, List

from src.tools.security import is_command_safe, is_path_safe
from config import ALLOWED_FILE_DIRS

logger = logging.getLogger("jarvis.tools.os")

# --- apps / system ---

def open_app(app_name: str) -> Dict[str, Any]:
    clean_name = app_name.strip()
    if not clean_name:
        return {"success": False, "message": "App name cannot be empty"}

    try:
        res = subprocess.run(["open", "-a", clean_name], capture_output=True, text=True)
        if res.returncode == 0:
            return {"success": True, "message": f"Opened application '{clean_name}'"}

        # some apps don't play nice with `open -a`, try activating via AppleScript instead
        script = f'tell application "{clean_name}" to activate'
        res_apple = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res_apple.returncode == 0:
            return {"success": True, "message": f"Activated application '{clean_name}'"}

        return {"success": False, "message": f"Could not open '{clean_name}': {res_apple.stderr.strip()}"}
    except Exception as e:
        return {"success": False, "message": f"Error opening app '{clean_name}': {e}"}


def quit_app(app_name: str) -> Dict[str, Any]:
    clean_name = app_name.strip()
    try:
        script = f'tell application "{clean_name}" to quit'
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            return {"success": True, "message": f"Quit application '{clean_name}'"}
        return {"success": False, "message": f"Failed to quit '{clean_name}': {res.stderr.strip()}"}
    except Exception as e:
        return {"success": False, "message": f"Error quitting '{clean_name}': {e}"}


def set_volume(level: int) -> Dict[str, Any]:
    target = max(0, min(100, int(level)))
    try:
        script = f"set volume output volume {target}"
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            return {"success": True, "message": f"System volume set to {target}%"}
        return {"success": False, "message": f"Error setting volume: {res.stderr.strip()}"}
    except Exception as e:
        return {"success": False, "message": f"Volume control exception: {e}"}


def get_volume() -> Dict[str, Any]:
    try:
        script = "output volume of (get volume settings)"
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode != 0:
            return {"success": False, "message": "Failed to read system volume"}
        vol = int(res.stdout.strip())
        return {"success": True, "volume": vol, "message": f"Current system volume is {vol}%"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def run_shell_command(cmd: str) -> Dict[str, Any]:
    # security.py does the actual gatekeeping here, this just calls into it
    safe, reason = is_command_safe(cmd)
    if not safe:
        return {"success": False, "message": f"Command rejected: {reason}"}

    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5.0)
        output = res.stdout.strip() or res.stderr.strip() or "Command completed with no output."
        return {"success": res.returncode == 0, "output": output[:1000]}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Command execution timed out"}
    except Exception as e:
        return {"success": False, "message": f"Execution error: {e}"}


# --- files ---

def search_files(keyword: str, base_folder: str = "Documents") -> Dict[str, Any]:
    target_dir = Path.home() / base_folder
    safe, resolved_path = is_path_safe(str(target_dir))

    if not safe:
        return {"success": False, "message": f"Folder '{base_folder}' is outside allowed directories."}

    matches: List[str] = []
    kw_lower = keyword.lower()

    try:
        if not resolved_path.exists():
            return {"success": False, "message": f"Directory '{resolved_path}' does not exist."}

        for root, _, files in os.walk(resolved_path):
            for file in files:
                if kw_lower in file.lower() and not file.startswith("."):
                    matches.append(str(Path(root) / file))
                    if len(matches) >= 15:
                        break
            if len(matches) >= 15:
                break

        return {
            "success": True,
            "keyword": keyword,
            "count": len(matches),
            "files": matches,
            "message": f"Found {len(matches)} matching file(s) for '{keyword}'"
        }
    except Exception as e:
        return {"success": False, "message": f"Error searching files: {e}"}


def read_file_content(filepath: str, max_lines: int = 50) -> Dict[str, Any]:
    safe, resolved = is_path_safe(filepath)
    if not safe:
        return {"success": False, "message": f"Access denied to file path '{filepath}'."}

    if not resolved.exists() or not resolved.is_file():
        return {"success": False, "message": f"File does not exist: '{filepath}'"}

    try:
        lines: List[str] = []
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append("... [truncated]")
                    break
                lines.append(line)

        content = "".join(lines)
        return {
            "success": True,
            "filepath": str(resolved),
            "content": content,
            "message": f"Successfully read {len(lines)} line(s) from {resolved.name}"
        }
    except Exception as e:
        return {"success": False, "message": f"Error reading file '{filepath}': {e}"}


# --- browser ---

def open_google_search(query: str) -> Dict[str, Any]:
    # handles the "search X" / "google X" intent from brain.py
    clean_query = query.strip()
    if not clean_query:
        return {"success": False, "message": "Search query cannot be empty"}

    try:
        encoded_query = urllib.parse.quote(clean_query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        res = subprocess.run(["open", search_url], capture_output=True, text=True)

        if res.returncode == 0:
            logger.info(f"Opened web browser for query: {clean_query}")
            return {
                "success": True,
                "url": search_url,
                "message": f"Opened browser search results for '{clean_query}'"
            }
        return {"success": False, "message": f"Failed to open browser: {res.stderr.strip()}"}
    except Exception as e:
        logger.error(f"Browser launch exception: {e}")
        return {"success": False, "message": f"Browser launch error: {e}"}
