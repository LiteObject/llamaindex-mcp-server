#!/usr/bin/env python3
"""
LlamaIndex Documentation MCP Server
Fetches and serves LlamaIndex documentation for VS Code Copilot integration
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class LlamaIndexDocServer:
    """Server for fetching and searching LlamaIndex documentation resources."""

    def __init__(self):
        """Initialize the LlamaIndexDocServer with base URL, HTTP client, and resource cache."""
        self.base_url = "https://docs.llamaindex.ai"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cached_docs = {}
        self.resources = []

    async def initialize(self):
        """Initialize the server and fetch initial documentation structure."""
        try:
            await self._fetch_doc_structure()
            logger.info(
                "Initialized with %d documentation resources", len(self.resources))
        except httpx.HTTPStatusError as e:
            logger.error("HTTP status error during initialization: %s", e)
        except httpx.RequestError as e:
            logger.error("HTTP request error during initialization: %s", e)
        except (AttributeError, TypeError, ValueError) as e:
            logger.error("Unexpected error during initialization: %s", e)

    async def _fetch_doc_structure(self):
        """Fetch the documentation structure from LlamaIndex docs."""
        try:
            response = await self.client.get(f"{self.base_url}/en/stable/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find navigation links and main content sections
            nav_links = soup.find_all('a', href=True)
            doc_links = []

            for link in nav_links:
                href = link.get('href')
                if href and (href.startswith('/') or href.startswith('http')):
                    if 'docs.llamaindex.ai' in href or href.startswith('/'):
                        full_url = urljoin(self.base_url, href)
                        title = link.get_text(strip=True)
                        if title and len(title) > 3:  # Filter out short/empty titles
                            doc_links.append((full_url, title))

            # Create resources from discovered links
            seen_urls = set()
            # Limit to first 50 to avoid overwhelming
            for url, title in doc_links[:50]:
                if url not in seen_urls:
                    seen_urls.add(url)
                    resource = MCPResource(
                        uri=url,
                        name=f"llamaindex_doc_{len(self.resources)}",
                        description=f"LlamaIndex Documentation: {title}",
                        mime_type="text/html"
                    )
                    self.resources.append(resource)

        except httpx.RequestError as e:
            logger.error("HTTP error fetching doc structure: %s", e)
            self._add_default_resources()
        except (AttributeError, TypeError, ValueError) as e:
            logger.error("Unexpected error fetching doc structure: %s", e)
            self._add_default_resources()

    def _add_default_resources(self):
        """Add default LlamaIndex documentation resources."""
        default_docs = [
            ("/en/stable/getting_started/starter_example.html", "Getting Started"),
            ("/en/stable/module_guides/loading/", "Data Loading"),
            ("/en/stable/module_guides/indexing/", "Indexing"),
            ("/en/stable/module_guides/querying/", "Querying"),
            ("/en/stable/module_guides/agents/", "Agents"),
        ]

        for path, title in default_docs:
            resource = MCPResource(
                uri=f"{self.base_url}{path}",
                name=f"llamaindex_{title.lower().replace(' ', '_')}",
                description=f"LlamaIndex Documentation: {title}",
                mime_type="text/html"
            )
            self.resources.append(resource)

    async def fetch_resource_content(self, uri: str) -> str:
        """Fetch content for a specific documentation resource by URI."""
        if uri in self.cached_docs:
            return self.cached_docs[uri]

        try:
            response = await self.client.get(uri)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract main content (remove navigation, sidebar, etc.)
            main_content = soup.find('main') or soup.find(
                'article') or soup.find('div', class_='content')

            if main_content:
                # Remove script and style elements
                for script in main_content(["script", "style", "nav", "header", "footer"]):
                    script.decompose()

                content = main_content.get_text(separator='\n', strip=True)
            else:
                content = soup.get_text(separator='\n', strip=True)

            # Cache the content
            self.cached_docs[uri] = content
            return content

        except httpx.RequestError as e:
            logger.error("HTTP error fetching content from %s: %s", uri, e)
            return f"HTTP error fetching content: {str(e)}"
        except httpx.HTTPError as e:
            logger.error("HTTP error fetching content from %s: %s", uri, e)
            return f"HTTP error fetching content: {str(e)}"
        except (AttributeError, TypeError, ValueError) as e:
            logger.error(
                "Unexpected error fetching content from %s: %s", uri, e)
            return f"Unexpected error fetching content: {str(e)}"

    async def search_documentation(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search through cached documentation for a query string."""
        results = []
        query_lower = query.lower()

        for resource in self.resources:
            if query_lower in resource.description.lower() or query_lower in resource.name.lower():
                content = await self.fetch_resource_content(resource.uri)
                if query_lower in content.lower():
                    # Find relevant snippet
                    lines = content.split('\n')
                    relevant_lines = [
                        line for line in lines if query_lower in line.lower()]
                    # First 3 matching lines
                    snippet = '\n'.join(relevant_lines[:3])

                    results.append({
                        'uri': resource.uri,
                        'title': resource.description,
                        'snippet': snippet[:200] + '...' if len(snippet) > 200 else snippet
                    })

                    if len(results) >= limit:
                        break

        return results


class MCPServer:
    """Main server class for handling MCP requests and documentation tools."""

    def __init__(self):
        """Initialize the MCP server with documentation tools."""
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

    async def initialize(self):
        """Initialize the documentation server and tools."""
        await self.doc_server.initialize()

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests and dispatch to the appropriate method or tool."""
        logger.info("Received request: %s", request)
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")  # CRITICAL: Extract the request ID

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
                    raise ValueError("URI parameter is required")

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
                    raise ValueError(f"Unknown tool: {tool_name}")

            else:
                raise ValueError(f"Unknown method: {method}")

            # Return proper JSON-RPC 2.0 response
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
        except (TypeError, RuntimeError, httpx.HTTPError) as e:
            logger.error("Error handling request: %s", e)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }


mcp_server = MCPServer()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan event handler for FastAPI app. Initializes the MCP server on startup."""
    logger.info("Starting MCP Server initialization...")
    await mcp_server.initialize()
    logger.info("MCP Server initialized and ready for HTTP requests.")
    yield
    logger.info("MCP Server shutting down...")

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    """Root endpoint for basic server status."""
    return JSONResponse(content={"status": "MCP Server is running", "version": "1.0.0"})


@app.get("/rpc")
async def rpc_healthcheck():
    """Healthcheck endpoint for /rpc (GET). Returns 200 OK."""
    return JSONResponse(content={"status": "ok", "method": "GET /rpc healthcheck"})


@app.post("/rpc")
async def rpc_endpoint(request: Request):
    """HTTP POST endpoint for MCP JSON-RPC requests. Accepts a JSON body and returns the server response."""
    logger.info("Received POST /rpc request")
    try:
        req_json = await request.json()
        logger.info("Request JSON: %s", req_json)

        # Validate basic JSON-RPC structure
        if "method" not in req_json:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": req_json.get("id"),
                    "error": {"code": -32600, "message": "Invalid Request: missing method"}
                },
                status_code=400
            )

        response = await mcp_server.handle_request(req_json)
        logger.info("Response: %s", response)
        return JSONResponse(content=response)

    except (json.JSONDecodeError, TypeError) as e:
        logger.error("Invalid JSON in /rpc endpoint: %s", e)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            },
            status_code=400
        )
    except httpx.HTTPError as e:
        logger.error("HTTP error in /rpc endpoint: %s", e)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": f"HTTP error: {str(e)}"}
            },
            status_code=502
        )
    except Exception as e:
        logger.error("Unexpected error in /rpc endpoint: %s", e, exc_info=True)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            },
            status_code=500
        )


if __name__ == "__main__":
    """Entry point for running the FastAPI server with Uvicorn."""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
