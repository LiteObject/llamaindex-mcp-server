# LlamaIndex Documentation MCP Server

A Model Context Protocol (MCP) server that fetches and serves LlamaIndex documentation for VS Code Copilot integration. This server runs in a Docker container and provides searchable access to LlamaIndex documentation.

## Features

- 🔍 Search through LlamaIndex documentation
- 📚 Fetch specific documentation resources
- 🐳 Containerized for easy deployment
- 🔧 VS Code Copilot integration
- ⚡ Async HTTP client for fast fetching
- 💾 Content caching for improved performance

## Prerequisites

- Docker and Docker Compose installed
- VS Code with Copilot extension
- Python 3.11+ (for local development)

## Quick Start

1. **Clone or create the project structure:**
   ```bash
   mkdir llamaindex-mcp-server
   cd llamaindex-mcp-server
   ```

2. **Create all the necessary files** (main.py, requirements.txt, Dockerfile, etc.)

3. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

4. **Configure VS Code:**
   Add the MCP server configuration to your VS Code settings:
   ```json
   {
     "mcpServers": {
       "llamaindex-docs": {
         "command": "docker",
         "args": [
           "run",
           "--rm",
           "-i",
           "--name", "llamaindex-mcp-server",
           "llamaindex-mcp-server:latest"
         ],
         "env": {
           "PYTHONUNBUFFERED": "1"
         }
       }
     }
   }
   ```

5. **Restart VS Code** to load the MCP server.

## Manual Setup

### Build the Docker Image

```bash
docker build -t llamaindex-mcp-server .
```

### Run the Container

**Interactive mode (for testing):**
```bash
docker run --rm -i llamaindex-mcp-server
```

**With Docker Compose:**
```bash
docker-compose up -d
```

## Usage

Once configured, the MCP server provides the following tools to VS Code Copilot:

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

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run locally:**
   ```bash
   python main.py
   ```

3. **Test with sample MCP requests:**
   ```bash
   echo '{"method": "initialize", "params": {}}' | python main.py
   ```

### Docker Development

**Build and test:**
```bash
docker build -t llamaindex-mcp-server .
docker run --rm -it llamaindex-mcp-server
```

**Debug container:**
```bash
docker run --rm -it llamaindex-mcp-server /bin/bash
```

## Configuration

### Environment Variables

- `PYTHONUNBUFFERED=1` - Ensures Python output is not buffered
- Custom timeout and retry settings can be added to the HTTP client

### VS Code MCP Configuration

The server can be configured in VS Code's settings.json:

```json
{
  "mcpServers": {
    "llamaindex-docs": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "llamaindex-mcp-server:latest"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Container fails to start:**
   - Check Docker is running
   - Verify the image was built successfully
   - Check container logs: `docker logs llamaindex-mcp-server`

2. **VS Code doesn't recognize the MCP server:**
   - Ensure the configuration is in the correct settings.json
   - Restart VS Code completely
   - Check VS Code developer console for errors

3. **Documentation fetching fails:**
   - Check internet connectivity from container
   - Verify LlamaIndex docs are accessible
   - Check container logs for HTTP errors

### Debugging

**View container logs:**
```bash
docker logs llamaindex-mcp-server
```

**Execute commands in running container:**
```bash
docker exec -it llamaindex-mcp-server /bin/bash
```

**Test HTTP connectivity:**
```bash
docker run --rm llamaindex-mcp-server python -c "import httpx; print(httpx.get('https://docs.llamaindex.ai').status_code)"
```

## Architecture

```
VS Code Copilot
      ↓
   MCP Protocol
      ↓
  Docker Container
      ↓
  Python MCP Server
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