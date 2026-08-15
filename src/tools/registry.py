import logging
from typing import Dict, Any, List
from src.tools.system import open_app, quit_app, set_volume, get_volume, run_shell_command
from src.tools.browser import open_google_search
from src.tools.filesystem import search_files, read_file_content

logger = logging.getLogger("jarvis.tools.registry")

# Tool Schemas for Function Calling (Ollama compatible)
TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open or activate a macOS application by name (e.g. Safari, Calculator, Notes, Terminal).",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to open"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "quit_app",
            "description": "Quit a running macOS application by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to quit"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Set macOS system audio volume to a percentage level between 0 and 100.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Volume level from 0 (mute) to 100"}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_volume",
            "description": "Retrieve current macOS audio volume setting.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_google_search",
            "description": "Open default web browser to Google search results for a specific query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files in user folders matching a keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Keyword or filename pattern"},
                    "base_folder": {"type": "string", "description": "Folder to search in: Documents, Desktop, or Downloads"}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": "Read text content from a specified file inside user directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file to read"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": "Execute a safe macOS diagnostic shell command from allowlist (date, uptime, sw_vers, whoami, df, ls, ping).",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "Allowed shell command string"}
                },
                "required": ["cmd"]
            }
        }
    }
]

def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Central tool execution dispatcher."""
    logger.info(f"Executing tool '{name}' with args: {args}")
    
    if name == "open_app":
        return open_app(args.get("app_name", ""))
    elif name == "quit_app":
        return quit_app(args.get("app_name", ""))
    elif name == "set_volume":
        return set_volume(args.get("level", 50))
    elif name == "get_volume":
        return get_volume()
    elif name == "open_google_search":
        return open_google_search(args.get("query", ""))
    elif name == "search_files":
        return search_files(args.get("keyword", ""), args.get("base_folder", "Documents"))
    elif name == "read_file_content":
        return read_file_content(args.get("filepath", ""))
    elif name == "run_shell_command":
        return run_shell_command(args.get("cmd", ""))
    else:
        return {"success": False, "message": f"Unknown tool: {name}"}
