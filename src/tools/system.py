import subprocess
import logging
from typing import Dict, Any
from src.tools.security import is_command_safe

logger = logging.getLogger("jarvis.tools.system")

def open_app(app_name: str) -> Dict[str, Any]:
    """Open or bring to front a macOS application by name."""
    clean_name = app_name.strip()
    if not clean_name:
        return {"success": False, "message": "App name cannot be empty"}

    try:
        # Try open -a first
        res = subprocess.run(["open", "-a", clean_name], capture_output=True, text=True)
        if res.returncode == 0:
            return {"success": True, "message": f"Opened application '{clean_name}'"}
        
        # Fallback to AppleScript
        script = f'tell application "{clean_name}" to activate'
        res_apple = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res_apple.returncode == 0:
            return {"success": True, "message": f"Activated application '{clean_name}'"}
        
        return {"success": False, "message": f"Could not open '{clean_name}': {res_apple.stderr.strip()}"}
    except Exception as e:
        return {"success": False, "message": f"Error opening app '{clean_name}': {e}"}

def quit_app(app_name: str) -> Dict[str, Any]:
    """Quit a running macOS application by name."""
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
    """Set macOS system audio volume level (0-100)."""
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
    """Retrieve current macOS system audio volume level."""
    try:
        script = "output volume of (get volume settings)"
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            vol = int(res.stdout.strip())
            return {"success": True, "volume": vol, "message": f"Current system volume is {vol}%"}
        return {"success": False, "message": "Failed to read system volume"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def run_shell_command(cmd: str) -> Dict[str, Any]:
    """Execute a safe shell command from the security allowlist."""
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
