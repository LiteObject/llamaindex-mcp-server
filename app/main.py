#!/usr/bin/env python3
"""
LlamaIndex Documentation MCP Server
Fetches and serves LlamaIndex documentation for VS Code Copilot integration
"""

import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .middleware import log_requests
from .mcp_server import MCPServer
from .routes import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
"""FastAPI application instance for the MCP server."""

# Register logging middleware
app.middleware("http")(log_requests)

# Register API routes
app.include_router(api_router)

if __name__ == "__main__":
    """Entry point for running the FastAPI server with Uvicorn."""
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
