"""
MCP server module for handling LlamaIndex documentation requests and tool invocations.
"""

import json
import logging
from typing import Any, Dict

from .llamaindex_doc_server import LlamaIndexDocServer
from .models import MCPTool

logger = logging.getLogger(__name__)


class MCPServer:
    """
    Main server class for handling MCP requests and documentation tools.
    Provides endpoints for initialization, resource listing/reading, and tool execution.
    """

    def __init__(self):
        """
        Initialize the MCP server with documentation server and available tools.
        """
        self.doc_server = LlamaIndexDocServer()
        self.tools = [
            MCPTool(
                name="search_llamaindex_docs",
                description="Search through LlamaIndex documentation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for LlamaIndex documentation"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
            MCPTool(
                name="get_llamaindex_resource",
                description="Get the full content of a specific LlamaIndex documentation resource",
                input_schema={
                    "type": "object",
                    "properties": {
                        "uri": {
                            "type": "string",
                            "description": "URI of the documentation resource to fetch"
                        }
                    },
                    "required": ["uri"]
                }
            )
        ]

    async def initialize(self, resource_limit: int = 50):
        """
        Initialize the documentation server and load resources.

        Args:
            resource_limit (int): Maximum number of resources to fetch (default: 50).
        """
        await self.doc_server.initialize(resource_limit)

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP requests and return appropriate responses.

        Args:
            request: MCP request dictionary containing method, params, and id

        Returns:
            MCP response dictionary with result or error
        """
        logger.info("Received request: %s", request)
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        try:
            result = None
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "resources": {"subscribe": True, "listChanged": True},
                        "tools": {"listChanged": True}
                    },
                    "serverInfo": {
                        "name": "llamaindex-docs-server",
                        "version": "1.0.0"
                    }
                }
            elif method == "resources/list":
                result = {
                    "resources": [
                        {
                            "uri": r.uri,
                            "name": r.name,
                            "description": r.description,
                            "mimeType": r.mime_type
                        }
                        for r in self.doc_server.resources
                    ]
                }
            elif method == "resources/read":
                uri = params.get("uri")
                if not uri:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Invalid params: URI parameter is required"
                        }
                    }
                content = await self.doc_server.fetch_resource_content(uri)
                result = {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "text/plain",
                            "text": content
                        }
                    ]
                }
            elif method == "tools/list":
                result = {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.input_schema
                        }
                        for tool in self.tools
                    ]
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                if tool_name == "search_llamaindex_docs":
                    query = arguments.get("query")
                    limit = arguments.get("limit", 5)
                    results = await self.doc_server.search_documentation(query, limit)
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(results, indent=2)
                            }
                        ]
                    }
                elif tool_name == "get_llamaindex_resource":
                    uri = arguments.get("uri")
                    content = await self.doc_server.fetch_resource_content(uri)
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": content
                            }
                        ]
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: Unknown tool {tool_name}"
                        }
                    }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            logger.info("Sending response: %s", response)
            return response
        except ValueError as e:
            logger.error("Value error handling request: %s", e)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": str(e)
                }
            }
        except KeyError as e:
            logger.error("Key error handling request: %s", e)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Missing key: {str(e)}"
                }
            }
        except (TypeError, RuntimeError) as e:
            logger.error("Error handling request: %s", e)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
