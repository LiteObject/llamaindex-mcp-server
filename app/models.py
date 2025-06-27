"""
Data models for MCP server resources and tools.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class MCPResource:
    """
    Represents a documentation resource for the MCP server.

    Attributes:
        uri (str): The URI of the documentation resource.
        name (str): The name of the resource.
        description (str): A human-readable description of the resource.
        mime_type (str): The MIME type of the resource content (default: "text/plain").
    """
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


@dataclass
class MCPTool:
    """
    Represents a tool that can be used by the MCP server.

    Attributes:
        name (str): The name of the tool.
        description (str): A human-readable description of the tool.
        input_schema (Dict[str, Any]): The JSON schema for the tool's input parameters.
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
