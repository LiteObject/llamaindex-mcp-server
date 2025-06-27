"""
API route handlers for the MCP server FastAPI application.
Defines endpoints for health, status, and JSON-RPC requests.
"""

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .mcp_server import MCPServer

logger = logging.getLogger(__name__)

router = APIRouter()
"""APIRouter instance for registering MCP server endpoints."""
# Use a single shared MCPServer instance for the app
mcp_server = MCPServer()


@router.get("/")
async def root():
    """
    Root endpoint for basic server status.
    Returns:
        JSONResponse: Status and version information for the MCP server.
    """
    return JSONResponse(content={"status": "MCP Server is running", "version": "1.0.0"})


@router.get("/rpc")
async def rpc_healthcheck():
    """
    Healthcheck endpoint for /rpc (GET). Returns 200 OK if the server is running.
    Returns:
        JSONResponse: Healthcheck status for the /rpc endpoint.
    """
    return JSONResponse(content={"status": "ok", "method": "GET /rpc healthcheck"})


@router.post("/rpc")
async def rpc_endpoint(request: Request):
    """
    HTTP POST endpoint for MCP JSON-RPC requests. Accepts a JSON body and returns the server response.
    Args:
        request (Request): The incoming FastAPI request containing the JSON-RPC body.
    Returns:
        JSONResponse: The server's response to the JSON-RPC request.
    """
    logger.info("Received POST /rpc request")
    try:
        try:
            req_json = await request.json()
        except RequestValidationError:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error: Invalid JSON"}
                },
                status_code=400
            )
        except json.JSONDecodeError:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error: Invalid JSON"}
                },
                status_code=400
            )
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
    except RequestValidationError:
        logger.error("Request validation error", exc_info=True)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Request validation error"}
            },
            status_code=400
        )
    except json.JSONDecodeError:
        logger.error("JSON decode error in /rpc endpoint", exc_info=True)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error: Invalid JSON"}
            },
            status_code=400
        )
    except RuntimeError:
        logger.error("Runtime error in /rpc endpoint", exc_info=True)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": "Internal server error"}
            },
            status_code=500
        )


@router.api_route("/rpc", methods=["PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def rpc_method_not_allowed(request: Request):
    """
    Handler for unsupported HTTP methods on /rpc. Returns 405 Method Not Allowed.
    Args:
        request: The incoming FastAPI request.
    Returns:
        JSONResponse: 405 Method Not Allowed response.
    """
    return JSONResponse(status_code=405, content={"detail": "Method Not Allowed"})
