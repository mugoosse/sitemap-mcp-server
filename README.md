<h1 align="center">Sitemap MCP Server</h1>

<p align="center">A powerful Model Context Protocol (MCP) server for sitemap analysis and visualization</p>

## Overview

The Sitemap MCP Server provides AI agents and MCP clients with powerful tools for fetching, parsing, analyzing, and visualizing website sitemaps. It handles all standard sitemap formats including XML, Google News, and plain text sitemaps.

## MCP Server primitives

### Tools

| Tool | Description |
|------|-------------|
| `get_sitemap_tree` | Fetch and parse the complete sitemap hierarchy |
| `get_sitemap_pages` | Extract all pages with filtering options (by route or specific subsitemap) |
| `get_sitemap_stats` | Generate comprehensive sitemap statistics with per-subsitemap details |
| `parse_sitemap_content` | Parse sitemap directly from content |

### Prompts

The server includes ready-to-use prompts for common sitemap tasks:

| Prompt | Purpose |
|--------|--------|
| `analyze_sitemap` | Comprehensive structure analysis |
| `sitemap_health_check` | SEO and health assessment |
| `extract_sitemap_urls` | Extract and filter specific URLs |
| `sitemap_missing_analysis` | Identify content gaps |
| `visualize_sitemap` | Create Mermaid.js diagram visualizations of sitemap structure |

## Installation

### Prerequisites

- Python 3.12+ (for non-Docker installation)
- Docker (optional, but recommended for simplest setup)

### Quick Start (TL;DR)

1. **Install the server**: Use Docker (recommended) or Python
2. **Configure your client**: Add the MCP server to your AI assistant
3. **Start using**: Access sitemap tools and resources through your AI assistant

### Server Installation

Choose **one** of the following options to install and run the Sitemap MCP Server:

#### Option 1: Using Docker

The simplest way to get started with minimal configuration:

```bash
# Build the Docker image (required before any Docker-based connections)
docker build -t mcp/sitemap --build-arg PORT=8050 .
```



#### Option 2: Using uv

For faster dependency resolution with uv:

```bash
# Clone the repository
git clone https://github.com/mugoosse/sitemap-mcp-server.git
cd sitemap-mcp-server

# Install uv if you don't have it already
curl -LSfs https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install dependencies in one step
uv sync

# Set up configuration
cp .env.example .env
```

### Build the Docker Image

If you plan to use Docker for connecting to the MCP server, you need to build the image first:

> **Prerequisite**: Make sure Docker is installed and running on your system.

```bash
docker build -t mcp/sitemap --build-arg PORT=8050 .
```

### Client Configuration

Choose the appropriate configuration based on your AI assistant client:

#### Option 1: Claude Desktop

1. Locate your Claude configuration file:
   - On Mac: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
   - On Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - On Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add one of these configurations to your `claude_desktop_config.json`:

   **Option A: Using Docker (recommended)**
   ```json
   {
     "mcpServers": {
       "sitemap": {
         "command": "docker",
         "args": ["run", "-i", "--rm", "--name", "sitemap-mcp-server", "-e", "TRANSPORT=stdio", "mcp/sitemap"],
         "env": { "TRANSPORT": "stdio" }
       }
     }
   }
   ```
   > **Important**: Make sure Docker is installed and running on your system for this configuration to work.

   **Option B: Using uv**
   ```json
   {
     "mcpServers": {
       "sitemap": {
         "command": "uv",
         "args": [
           "run",
           "--with",
           "mcp[cli]",
           "mcp",
           "run",
           "/path/to/sitemap-mcp-server/src/main.py"
         ]
       }
     }
   }
   ```
   > **Note**: Update the path to match your local installation

3. Restart Claude if it's running

#### Option 2: Cursor

Add this configuration to your Cursor settings:

```json
{
  "mcpServers": {
    "sitemap": {
      "transport": "sse",
      "url": "http://localhost:8050/sse"
    }
  }
}
```

> **Important**: For SSE connections, you must first start the server separately with one of these commands:
> 
> **Using Docker:**
> ```bash
> docker run -i --rm --name sitemap-mcp-server -p 8050:8050 mcp/sitemap
> ```
> 
> **Using Python or uv:**
> ```bash
> # From the project directory
> python src/main.py
> # or
> uv run src/main.py
> ```

#### Option 3: Other MCP Clients

For other MCP clients, use a permutation of the configurations covered above:

- For SSE connections: Use the same approach as the Cursor configuration, adjusting the URL format if needed (some clients require `serverUrl` instead of `url`)
- For stdio connections: Use either the Docker or uv approach from the Claude Desktop configuration

Remember that SSE connections require starting the server separately as described in the Cursor section.

### Configuration Options

Customize your server by setting these environment variables:

| Variable | Purpose | Default | Notes |
|----------|---------|--------|--------|
| `TRANSPORT` | Connection method (`sse` or `stdio`) | `sse` | **Critical**: This determines how the server communicates. Set to `stdio` for direct stdio connections, or `sse` for Server-Sent Events. For Docker stdio connections, this is set via the `-e "TRANSPORT=stdio"` parameter in our examples. |
| `HOST` | Server address for SSE mode | `0.0.0.0` | Only used when `TRANSPORT=sse` |
| `PORT` | Server port for SSE mode | `8050` | Only used when `TRANSPORT=sse` |
| `CACHE_MAX_AGE` | Sitemap cache duration (seconds) | `86400` (1 day) | |
| `LOG_LEVEL` | Log level (INFO, DEBUG, etc.) | `INFO` | |
| `LOG_FILE` | Log file name | `sitemap_server.log` | |

> **Important**: The `TRANSPORT` environment variable controls whether the server runs in SSE or stdio mode. Our Docker and uv configurations for Claude Desktop already set this correctly. If you're using a custom configuration, make sure to set this appropriately.


## Tool Usage Examples

### Fetch a Complete Sitemap

```json
{
  "name": "get_sitemap_tree",
  "arguments": {
    "url": "https://example.com",
    "include_pages": true
  }
}
```

### Get Pages with Filtering

#### Filter by Route
```json
{
  "name": "get_sitemap_pages",
  "arguments": {
    "url": "https://example.com",
    "limit": 100,
    "include_metadata": true,
    "route": "/blog/"
  }
}
```

#### Filter by Specific Subsitemap
```json
{
  "name": "get_sitemap_pages",
  "arguments": {
    "url": "https://example.com",
    "limit": 100,
    "include_metadata": true,
    "sitemap_url": "https://example.com/blog-sitemap.xml"
  }
}
```

#### Combine Both Filters
```json
{
  "name": "get_sitemap_pages",
  "arguments": {
    "url": "https://example.com",
    "limit": 50,
    "include_metadata": true,
    "route": "/blog/",
    "sitemap_url": "https://example.com/blog-sitemap.xml"
  }
}
```

### Get Sitemap Statistics

```json
{
  "name": "get_sitemap_stats",
  "arguments": {
    "url": "https://example.com"
  }
}
```

The response includes both total statistics and detailed stats for each subsitemap:

```json
{
  "total": {
    "url": "https://example.com",
    "page_count": 150,
    "sitemap_count": 3,
    "sitemap_types": ["WebsiteSitemap", "NewsSitemap"],
    "priority_stats": {
      "min": 0.1,
      "max": 1.0,
      "avg": 0.65
    },
    "last_modified_count": 120
  },
  "subsitemaps": [
    {
      "url": "https://example.com/sitemap.xml",
      "type": "WebsiteSitemap",
      "page_count": 100,
      "priority_stats": {
        "min": 0.3,
        "max": 1.0,
        "avg": 0.7
      },
      "last_modified_count": 80
    },
    {
      "url": "https://example.com/blog/sitemap.xml",
      "type": "WebsiteSitemap",
      "page_count": 50,
      "priority_stats": {
        "min": 0.1,
        "max": 0.9,
        "avg": 0.5
      },
      "last_modified_count": 40
    }
  ]
}
```

This allows MCP clients to understand which subsitemaps might be of interest for further investigation. You can then use the `sitemap_url` parameter in `get_sitemap_pages` to filter pages from a specific subsitemap.

### Parse Sitemap Content Directly

```json
{
  "name": "parse_sitemap_content",
  "arguments": {
    "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\"><url><loc>https://example.com/</loc></url></urlset>",
    "sitemap_url": "https://example.com/sitemap.xml"
  }
}
```

## Acknowledgements

- This MCP Server leverages the [ultimate-sitemap-parser](https://github.com/GateNLP/ultimate-sitemap-parser) library
- Built using the [Model Context Protocol](https://modelcontextprotocol.io) Python SDK