<div align="center">
    <img src="https://raw.githubusercontent.com/SmartFactory-KL/aas-mcp/main/docs/images/logo-aas-mcp-purple-500.png" alt="aas-mcp">
</div>

<div align="center">
  <a href="https://pypi.org/project/aas-mcp"><img src="https://img.shields.io/pypi/v/aas-mcp?color=%2334D058" alt="PyPI - Version"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
</div>

**aas-mcp** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides AI assistants with tools to interact with [Asset Administration Shells (AAS)](https://industrialdigitaltwin.org/en/content-hub/aasspecifications) via the [Eclipse BaSyx](https://www.eclipse.org/basyx/) REST API.

This MCP server enables AI assistants to perform full CRUD operations on AAS Shells, Submodels, and Submodel Elements, making it ideal for industrial automation, digital twin management, and AAS-based workflows.

### Features

- 🤖 **MCP Server** with 25+ tools for comprehensive AAS management
- 🔧 **Full CRUD Operations** on Shells, Submodels, and Submodel Elements
- ⚙️ **Health Monitoring** tools for AAS environment status
- 🔁 **Seamless Integration** with [Eclipse BaSyx](https://www.eclipse.org/basyx/) Environment REST API
- 📡 **AI-Ready** tools designed for intelligent automation workflows  

## 🚀 Installation

```bash
pip install aas-mcp
```

**Requires**: Python 3.10+

## 🚀 Usage

### Running the MCP Server

```bash
# Start the MCP server
aas-mcp
```

### HTTP Streaming mode + UI

Run the server via HTTP Streaming with a companion Gradio UI on a separate port:

```bash
# Default HTTP server 127.0.0.1:8000 and UI 127.0.0.1:7860
aas-mcp --transport http

# Custom MCP and UI hosts/ports
aas-mcp --transport http --host 0.0.0.0 --port 8765 \
        --ui-host 0.0.0.0 --ui-port 9000

# Disable UI if not needed
aas-mcp --transport http --no-ui
```

Environment variables:

- `AAS_MCP_TRANSPORT` = `stdio` (default) or `http`
- `AAS_MCP_HOST` = host to bind in HTTP mode (default `127.0.0.1`)
- `AAS_MCP_PORT` = port to bind in HTTP mode (default `8000`)
- `AAS_MCP_UI_HOST` = host for Gradio UI (default `127.0.0.1`)
- `AAS_MCP_UI_PORT` = port for Gradio UI (default `7860`)

## 🐳 Docker

Build and run the container exposing both the MCP HTTP server and the Gradio UI:

```bash
# Build
docker build -t aas-mcp:local .

# Run (maps MCP 8000 and UI 7860)
docker run --rm -p 8000:8000 -p 7860:7860 \
  -e SHELLSMITH_BASYX_ENV_HOST=http://host.docker.internal:8081 \
  --name aas-mcp aas-mcp:local
```

Using Docker Compose:

```bash
docker compose up --build
```

Environment variables you may want to set:

- `PORT` and `UI_PORT` to override container ports (mapped via compose)
- `SHELLSMITH_BASYX_ENV_HOST` to point at your BaSyx environment
- `AAS_MCP_*` to control transport/host/ports (defaults are set for HTTP+UI)

### Available Tools

The MCP server provides 25+ tools for AAS management:

#### Shell Management
- `get_shells` - Retrieve all AAS Shells
- `get_shell` - Get a specific Shell by ID
- `create_shell` - Create a new Shell
- `update_shell` - Update an existing Shell
- `delete_shell` - Delete a Shell

#### Submodel Management
- `get_submodels` - Retrieve all Submodels
- `get_submodel` - Get a specific Submodel by ID
- `create_submodel` - Create a new Submodel
- `update_submodel` - Update an existing Submodel
- `delete_submodel` - Delete a Submodel
- `get_submodel_value` - Get Submodel raw value
- `update_submodel_value` - Update Submodel value
- `get_submodel_metadata` - Get Submodel metadata

#### Submodel Element Management
- `get_submodel_elements` - Get all elements from a Submodel
- `get_submodel_element` - Get a specific element by path
- `create_submodel_element` - Create a new element
- `update_submodel_element` - Update an existing element
- `delete_submodel_element` - Delete an element
- `get_submodel_element_value` - Get element raw value
- `update_submodel_element_value` - Update element value

#### Reference Management
- `get_submodel_refs` - Get Submodel references from a Shell
- `create_submodel_ref` - Create a Submodel reference
- `delete_submodel_ref` - Delete a Submodel reference

#### Health & Monitoring
- `get_health_status` - Check AAS environment health
- `is_healthy` - Boolean health check

## 🔧 Configuration

### MCP Client Configuration

To use this server with MCP clients like [Claude Desktop](https://claude.ai/download), add it to your client's configuration:

```json
{
  "mcpServers": {
    "aas-mcp": {
      "command": "aas-mcp",
      "env": {
        "SHELLSMITH_BASYX_ENV_HOST": "http://localhost:8081"
      }
    }
  }
}
```

> ℹ️ Change the value of `SHELLSMITH_BASYX_ENV_HOST` to match your BaSyx Environment host URL

The configuration format is similar for other MCP clients like LM Studio.

### BaSyx Environment Configuration

The MCP server connects to an Eclipse BaSyx environment. The default host is:

```
http://localhost:8081
```

You can override it in several ways:

- Set the environment variable:  
  ```bash
  export SHELLSMITH_BASYX_ENV_HOST=https://your-host:1234
  ```

- Create a `.env` file in your working directory with:  
  ```dotenv
  SHELLSMITH_BASYX_ENV_HOST=https://your-host:1234
  ```

Each tool also accepts a `host` parameter to override the default configuration dynamically.

### What the UI does

- Configure Engine: POST to `{engine_host}/api/mcp/register` with payload `{ "name": "aas-mcp", "mcp_url": "http://<mcp_host>:<mcp_port>" }` using the provided API key as Bearer token.
- Set ShellSmith Host: updates the ShellSmith BaSyx host (also sets `SHELLSMITH_BASYX_ENV_HOST`). Note: since default parameter values in tools are bound at import time, a server restart may be required for defaults to update unless the client passes the `host` parameter explicitly.

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for setup, testing, and coding standards.

