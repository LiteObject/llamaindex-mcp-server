"""
Middleware module for logging HTTP requests and responses in the MCP server.
"""
import logging
import json
from fastapi import Request
from fastapi.responses import JSONResponse

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
