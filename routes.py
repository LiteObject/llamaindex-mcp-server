"""
API route handlers for the MCP server FastAPI application.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging
from mcp_server import MCPServer

logger = logging.getLogger(__name__)

router = APIRouter()
"""APIRouter instance for registering MCP server endpoints."""
mcp_server = MCPServer()


@router.get("/")
async def root():
    """Root endpoint for basic server status."""
    return JSONResponse(content={"status": "MCP Server is running", "version": "1.0.0"})


@router.get("/rpc")
async def rpc_healthcheck():
    """Healthcheck endpoint for /rpc (GET). Returns 200 OK."""
    return JSONResponse(content={"status": "ok", "method": "GET /rpc healthcheck"})


@router.post("/rpc")
async def rpc_endpoint(request: Request):
    """
    HTTP POST endpoint for MCP JSON-RPC requests. Accepts a JSON body and returns the server response.

    Args:
        request: The incoming FastAPI request containing the JSON-RPC body.

    Returns:
        JSONResponse with the server's response to the JSON-RPC request.
    """
    logger.info("Received POST /rpc request")
    try:
        req_json = await request.json()
        logger.info("Request JSON: %s", req_json)
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
    except (ValueError, TypeError) as e:
        logger.error("Error in /rpc endpoint: %s", e, exc_info=True)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            },
            status_code=500
        )
