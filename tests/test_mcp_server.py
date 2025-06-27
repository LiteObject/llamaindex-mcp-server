import pytest
import httpx

BASE_URL = "http://localhost:8000"


def docstring(text):
    """Decorator to add a docstring to a function."""
    def decorator(func):
        func.__doc__ = text
        return func
    return decorator


@docstring("Test the root endpoint for MCP server status.")
@pytest.mark.asyncio
async def test_root_status():
    """Test the root endpoint for MCP server status."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "MCP Server is running"


@docstring("Test the /rpc healthcheck endpoint for MCP server.")
@pytest.mark.asyncio
async def test_rpc_healthcheck():
    """Test the /rpc healthcheck endpoint for MCP server."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/rpc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


@docstring("Test the /rpc endpoint with the 'initialize' method for MCP server.")
@pytest.mark.asyncio
async def test_initialize_method():
    """Test the /rpc endpoint with the 'initialize' method for MCP server."""
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        resp = await client.post(f"{BASE_URL}/rpc", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["serverInfo"]["name"] == "llamaindex-docs-server"


@docstring("Test the /rpc POST endpoint with a valid method and parameters.")
@pytest.mark.asyncio
async def test_rpc_post_valid():
    """Test the /rpc POST endpoint with a valid method and parameters."""
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list",
            "params": {}
        }
        resp = await client.post(f"{BASE_URL}/rpc", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert "resources" in data["result"]
        assert isinstance(data["result"]["resources"], list)
