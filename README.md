# LlamaIndex Documentation MCP Server

A Model Context Protocol (MCP) server that fetches and serves LlamaIndex documentation for VS Code Copilot integration. This server now runs as an HTTP service (using FastAPI) and provides searchable access to LlamaIndex documentation.

## Features

- 🔍 Search through LlamaIndex documentation
- 📚 Fetch specific documentation resources
- 🐳 Containerized for easy deployment
- 🔧 VS Code Copilot integration
- ⚡ Async HTTP client for fast fetching
- 💾 Content caching for improved performance
- 🌐 HTTP API for multi-client (multi-VS Code) support

## Prerequisites

- Docker and Docker Compose installed
- VS Code with Copilot extension
- Python 3.11+ (for local development)

## Quick Start

1. **Clone or create the project structure:**
   ```bash
   git clone <repo-url>
   cd llamaindex-mcp-server
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d --build
   ```
   - The service will be available at `http://localhost:8000`.
   - The container will be named `mcp-server`.
   - The Docker image will be named `liteobject/llamaindex-mcp-server`.

### Healthcheck

The container exposes a healthcheck endpoint:

```
GET http://localhost:8000/rpc
```
Response:
```json
{"status": "ok", "method": "GET /rpc healthcheck"}
```

### Example: JSON-RPC Request

Send a JSON-RPC 2.0 request to the server:

```bash
curl -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}'
```

Example response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "resources": {"subscribe": true, "listChanged": true},
      "tools": {"listChanged": true}
    },
    "serverInfo": {
      "name": "llamaindex-docs-server",
      "version": "1.0.0"
    }
  }
}
```

## Environment Variables

- `PYTHONUNBUFFERED=1`
- `PYTHONPATH=/app`
- `UVICORN_LOG_LEVEL=warning`

## Usage

Once configured, the MCP server provides the following tools to VS Code Copilot via HTTP:

### Tools Available

1. **search_llamaindex_docs**
   - Search through LlamaIndex documentation
   - Parameters: `query` (string), `limit` (integer, optional)

2. **get_llamaindex_resource**
   - Get full content of a specific documentation resource
   - Parameters: `uri` (string)

### Resources Available

The server automatically discovers and provides access to:
- Getting Started guides
- Module guides (loading, indexing, querying)
- Agent documentation
- API references
- Examples and tutorials

## Development

To run locally without Docker:

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Common Issues

1. **Container fails to start:**
   - Check Docker is running
   - Verify the image was built successfully
   - Check container logs: `docker logs mcp-server`

2. **VS Code doesn't recognize the MCP server:**
   - Ensure the configuration is in the correct settings.json
   - Restart VS Code completely
   - Check VS Code developer console for errors

3. **Documentation fetching fails:**
   - Check internet connectivity from container
   - Verify LlamaIndex docs are accessible
   - Check container logs for HTTP errors

## Architecture

```
VS Code Copilot
      ↓
   MCP Protocol (HTTP)
      ↓
  Docker Container / Python MCP Server (FastAPI)
      ↓
  LlamaIndex Docs API
```

The server implements the MCP protocol specification and provides:
- Resource management (documentation pages)
- Tool execution (search and fetch operations)
- Content caching and optimization
- Error handling and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker
5. Submit a pull request

## License

MIT License - feel free to use and modify as needed.

## Support

For issues related to:
- **MCP Protocol**: Check the MCP specification
- **VS Code Integration**: Check VS Code Copilot documentation
- **LlamaIndex Docs**: Check LlamaIndex documentation
- **This Server**: Create an issue in the repository