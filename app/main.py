#!/usr/bin/env python3
"""
LlamaIndex Documentation MCP Server
Fetches and serves LlamaIndex documentation for VS Code Copilot integration
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request as StarletteRequest
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .middleware import log_requests
from .routes import router as api_router
from .routes import mcp_server  # Import the shared instance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan event handler for FastAPI app. Initializes the MCP server on startup."""
    resource_limit = int(os.getenv("MCP_RESOURCE_LIMIT", "50"))
    logger.info("Starting MCP Server initialization...")
    await mcp_server.initialize(resource_limit)
    logger.info("MCP Server initialized and ready for HTTP requests.")
    yield
    logger.info("MCP Server shutting down...")

app = FastAPI(lifespan=lifespan)
"""FastAPI application instance for the MCP server."""


class RpcExceptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch all exceptions for /rpc requests and return a JSON-RPC error response.
    Ensures that any unhandled exception or 500 error is returned as a JSON-RPC error object.
    Also ensures that HTTP method not allowed (405) is returned as a proper HTTP error for /rpc.
    """

    async def dispatch(self, request, call_next):
        """
        Intercept /rpc requests, catch exceptions, and return JSON-RPC error responses.
        Args:
            request: The incoming Starlette/FastAPI request.
            call_next: The next middleware or route handler.
        Returns:
            JSONResponse: JSON-RPC error response or the original response.
        """
        if request.url.path == "/rpc":
            # If method is not POST or GET, return 405 Method Not Allowed immediately
            if request.method not in ("POST", "GET"):
                return JSONResponse(
                    status_code=405,
                    content={"detail": "Method Not Allowed"},
                )
            try:
                response = await call_next(request)
                # If response is 500, replace with JSON-RPC error
                if response.status_code == 500:
                    return JSONResponse(
                        status_code=500,
                        content={
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {"code": -32603, "message": "Internal error"}
                        },
                    )
                return response
            except (StarletteHTTPException, RequestValidationError) as exc:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32603, "message": f"Internal error: {str(exc)}"}
                    },
                )
        return await call_next(request)


# Register logging middleware
app.middleware("http")(log_requests)
# Register RPC exception middleware
app.add_middleware(RpcExceptionMiddleware)

# Register API routes
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: StarletteRequest, exc: RequestValidationError):
    """
    Global exception handler for FastAPI request validation errors.
    Returns a JSON-RPC error response with code -32600 and status 400.
    Args:
        request: The incoming request.
        exc: The validation exception.
    Returns:
        JSONResponse: JSON-RPC error response.
    """
    return JSONResponse(
        status_code=400,
        content={
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": f"Request validation error: {exc.errors()}"}
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: StarletteRequest, exc: StarletteHTTPException):
    """
    Global exception handler for HTTP exceptions.
    For /rpc POST, returns a JSON-RPC parse error for status 400/422/500.
    Args:
        request: The incoming request.
        exc: The HTTP exception.
    Returns:
        JSONResponse: JSON-RPC error response or re-raises the exception.
    """
    # Only handle 400/422/500 for /rpc POST
    if request.url.path == "/rpc" and request.method == "POST" and exc.status_code in (400, 422, 500):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc.detail}"}
            },
        )
    raise exc

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
