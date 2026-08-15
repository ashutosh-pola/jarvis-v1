import shlex
from pathlib import Path
from typing import Tuple
from config import ALLOWED_COMMANDS, ALLOWED_FILE_DIRS

def is_command_safe(cmd_str: str) -> Tuple[bool, str]:
    """
    Validate shell command string against strict allowlist.
    Only allows approved diagnostic commands without dangerous subshells or redirects.
    """
    if not cmd_str or not cmd_str.strip():
        return False, "Empty command"

    # Reject dangerous operators (pipes, subshells, chaining)
    for forbidden in [";", "&&", "||", "|", "`", "$(", ">", "<", "\n"]:
        if forbidden in cmd_str:
            return False, f"Command contains forbidden character/operator '{forbidden}'"

    try:
        tokens = shlex.split(cmd_str)
        if not tokens:
            return False, "Invalid command formatting"
        
        base_cmd = Path(tokens[0]).name
        if base_cmd not in ALLOWED_COMMANDS:
            return False, f"Command '{base_cmd}' is not in the security allowlist ({', '.join(sorted(ALLOWED_COMMANDS))})"

        return True, "Safe"
    except Exception as e:
        return False, f"Command parsing error: {e}"

def is_path_safe(path_str: str) -> Tuple[bool, Path]:
    """
    Validate that file path resolves inside user-permitted directories.
    """
    try:
        resolved = Path(path_str).expanduser().resolve()
        
        # Check if resolved path starts with any allowed base dir
        for allowed_dir in ALLOWED_FILE_DIRS:
            allowed_resolved = allowed_dir.expanduser().resolve()
            if resolved == allowed_resolved or allowed_resolved in resolved.parents:
                return True, resolved

        return False, resolved
    except Exception:
        return False, Path(path_str)
