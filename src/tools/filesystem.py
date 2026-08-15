import os
from pathlib import Path
from typing import Dict, Any, List
import logging
from src.tools.security import is_path_safe
from config import ALLOWED_FILE_DIRS

logger = logging.getLogger("jarvis.tools.filesystem")

def search_files(keyword: str, base_folder: str = "Documents") -> Dict[str, Any]:
    """Search for matching files in permitted user folders."""
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
                    full_path = str(Path(root) / file)
                    matches.append(full_path)
                    if len(matches) >= 15:  # Limit search results
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
    """Safely read content from a text file within permitted directories."""
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
