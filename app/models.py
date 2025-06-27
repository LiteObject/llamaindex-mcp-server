from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class MCPResource:
    """Represents a documentation resource for the MCP server."""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


@dataclass
class MCPTool:
    """Represents a tool that can be used by the MCP server."""
    name: str
    description: str
    input_schema: Dict[str, Any]
