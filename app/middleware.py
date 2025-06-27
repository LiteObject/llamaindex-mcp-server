"""
Middleware module for logging HTTP requests and responses in the MCP server.
"""
import json
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


async def log_requests(request: Request, call_next):
    """
    Middleware to log all incoming HTTP requests and outgoing JSON responses.
    Args:
        request: The incoming FastAPI request.
        call_next: The next middleware or route handler.
    Returns:
        The FastAPI response object.
    """
    logger.info("Incoming request: %s %s", request.method, request.url)
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.body()
            logger.info("Request body: %s", body.decode('utf-8'))
        except (ValueError, RuntimeError) as e:
            logger.warning("Could not read request body: %s", e)
    response = await call_next(request)
    logger.info("Response status: %s", response.status_code)
    try:
        if response.headers.get("content-type", "").startswith("application/json"):
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            logger.info("Response body: %s", response_body.decode('utf-8'))
            return JSONResponse(content=json.loads(response_body), status_code=response.status_code)
    except (ValueError, json.JSONDecodeError) as e:
        logger.warning("Could not read response body: %s", e)
    return response


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
