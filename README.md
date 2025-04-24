# Sitemap MCP Server

Discover website architecture and analyze site structure by fetching, parsing, and visualizing sitemaps from any URL. Uncover hidden pages and extract organized hierarchies without manual exploration.

Includes ready-to-use prompt templates for Claude Desktop that let you analyze websites, check sitemap health, extract URLs, find missing content, and create visualizations with just a URL input.

![License](https://img.shields.io/github/license/mugoosse/sitemap-mcp-server)
![PyPI](https://img.shields.io/pypi/v/sitemap-mcp-server)
![Python Version](https://img.shields.io/badge/python-3.11+-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)
[![smithery badge](https://smithery.ai/badge/@mugoosse/sitemap)](https://smithery.ai/server/@mugoosse/sitemap)

<a href="https://glama.ai/mcp/servers/@mugoosse/sitemap-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@mugoosse/sitemap-mcp-server/badge" />
</a>

## Demo

Get answers to questions about any website leveraging the power of sitemaps.

<details><summary>Cursor: how many pages does a modelcontextprotocol.io have?</summary>

<br/>

<img width="1541" alt="image" src="https://github.com/user-attachments/assets/f234b35f-ccb2-44c6-8ce5-71a6d2531e43" />

</details>

<details><summary>Claude + prompt: visualize the sitemap in a diagram of windsurf.com</summary>

<br/>

Click on the "attach" button next to the tools button:

![image](https://github.com/user-attachments/assets/e5b558c7-85fa-4b8f-b108-6d66d3b20719)

Then select `visualize_sitemap`:

<img width="558" alt="image" src="https://github.com/user-attachments/assets/2106e720-52c3-48a3-aa64-fd9c0a6ab075" />

Now we enter windsurf.com:

![image](https://github.com/user-attachments/assets/ceddad25-3549-4a2f-a053-f54c1154912b)

And we get a visualization of teh sitemap:

<img width="1470" alt="image" src="https://github.com/user-attachments/assets/04464315-e619-4df5-8082-a981e6437da9" />

</details>

## Installation

Make sure [uv](https://docs.astral.sh/uv/getting-started/installation/) is installed.

### Installing in Claude Desktop, Cursor or Windsurf

Add this entry to your [claude_desktop_config.json](https://modelcontextprotocol.io/quickstart/user#2-add-the-filesystem-mcp-server), Cursor settings, etc.:

```json
{
  "mcpServers": {
    "sitemap": {
      "command": "uvx",
      "args": ["sitemap-mcp-server"],
      "env": { "TRANSPORT": "stdio" }
    }
  }
}
```

Restart Claude if it's running. For Cursor simply press refresh and/or enable the MCP Server in the settings.

### Installing via Smithery

To install sitemap for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@mugoosse/sitemap):

```bash
npx -y @smithery/cli install @mugoosse/sitemap --client claude
```

### MCP Inspector

<details><summary>uv + stdio transport</summary>

```bash
npx @modelcontextprotocol/inspector env TRANSPORT=stdio uvx sitemap-mcp-server
```

Open the MCP Inspector at http://127.0.0.1:6274, select `stdio` transport, and connect to the MCP server.

</details>

<details><summary>uv + sse transport</summary>

```bash
# Start the server
uvx sitemap-mcp-server

# Start the MCP Inspector in a separate terminal
npx @modelcontextprotocol/inspector connect http://127.0.0.1:8050
```

Open the MCP Inspector at http://127.0.0.1:6274, select `sse` transport, and connect to the MCP server.

</details>

### SSE Transport

If you want to use the SSE transport, follow these steps:

1. Start the server:

```bash
uvx sitemap-mcp-server
```

2. Configure your MCP Client, e.g. Cursor:

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

### Local Development

For instructions on building and running the project from source, please refer to the [DEVELOPERS.md](DEVELOPERS.md) guide.

## Usage

### Tools

The following tools are available via the MCP server:

- **get_sitemap_tree** - Fetch and parse the sitemap tree from a website URL

  - Arguments: `url` (website URL), `include_pages` (optional, boolean)
  - Returns: JSON representation of the sitemap tree structure

- **get_sitemap_pages** - Get all pages from a website's sitemap with filtering options

  - Arguments: `url` (website URL), `limit` (optional), `include_metadata` (optional), `route` (optional), `sitemap_url` (optional), `cursor` (optional)
  - Returns: JSON list of pages with pagination metadata

- **get_sitemap_stats** - Get statistics about a website's sitemap

  - Arguments: `url` (website URL)
  - Returns: JSON object with sitemap statistics including page counts, modification dates, and subsitemap details

- **parse_sitemap_content** - Parse a sitemap directly from its XML or text content
  - Arguments: `content` (sitemap XML content), `include_pages` (optional, boolean)
  - Returns: JSON representation of the parsed sitemap

### Prompts

The server includes ready-to-use prompts that appear as templates in Claude Desktop. After installing the server, you'll see these templates in the "Templates" menu (click the + icon next to the message input):

- **Analyze Sitemap**: Provides comprehensive structure analysis of a website's sitemap
- **Check Sitemap Health**: Evaluates SEO and health metrics of a sitemap
- **Extract URLs from Sitemap**: Extracts and filters specific URLs from a sitemap
- **Find Missing Content in Sitemap**: Identifies content gaps in a website's sitemap
- **Visualize Sitemap Structure**: Creates a Mermaid.js diagram visualization of sitemap structure

To use these prompts:

1. Click the + icon next to the message input in Claude Desktop
2. Select the desired template from the list
3. Fill in the website URL when prompted
4. Claude will execute the appropriate sitemap analysis

### Examples

#### Fetch a Complete Sitemap

```json
{
  "name": "get_sitemap_tree",
  "arguments": {
    "url": "https://example.com",
    "include_pages": true
  }
}
```

#### Get Pages with Filtering and Pagination

##### Filter by Route

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

##### Filter by Specific Subsitemap

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

##### Cursor-Based Pagination

The server implements MCP cursor-based pagination to handle large sitemaps efficiently:

**Initial Request:**

```json
{
  "name": "get_sitemap_pages",
  "arguments": {
    "url": "https://example.com",
    "limit": 50
  }
}
```

**Response with Pagination:**

```json
{
  "base_url": "https://example.com",
  "pages": [...],  // First batch of pages
  "limit": 50,
  "nextCursor": "eyJwYWdlIjoxfQ=="
}
```

**Subsequent Request with Cursor:**

```json
{
  "name": "get_sitemap_pages",
  "arguments": {
    "url": "https://example.com",
    "limit": 50,
    "cursor": "eyJwYWdlIjoxfQ=="
  }
}
```

When there are no more results, the `nextCursor` field will be absent from the response.

#### Get Sitemap Statistics

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

#### Parse Sitemap Content Directly

```json
{
  "name": "parse_sitemap_content",
  "arguments": {
    "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\"><url><loc>https://example.com/</loc></url></urlset>",
    "include_pages": true
  }
}
```

## Acknowledgements

- This MCP Server leverages the [ultimate-sitemap-parser](https://github.com/GateNLP/ultimate-sitemap-parser) library
- Built using the [Model Context Protocol](https://modelcontextprotocol.io) Python SDK

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
