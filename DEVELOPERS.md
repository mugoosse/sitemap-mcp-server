# Sitemap MCP Server - Developer Guide

This document provides detailed information for developers who want to contribute to the Sitemap MCP Server project. For general usage and installation instructions, please see the [README.md](README.md) file.

## Dev setup

Clone the repository:
```bash
git clone https://github.com/mugoosse/sitemap-mcp-server.git
cd sitemap-mcp-server
```

Make sure [uv](https://docs.astral.sh/uv/getting-started/installation/) is installed.

```bash
# Set up a virtual environment and install all dependencies (including dev and test dependencies)
uv sync --extra test --extra dev

# Set up environment variables
cp .env.example .env
```

## MCP Client setup

### MCP Inspector

<details><summary>uv + stdio transport</summary>

```bash
# Start the server (update the path)
npx @modelcontextprotocol/inspector env TRANSPORT=stdio uv --directory /path/to/sitemap-mcp-server run -m sitemap_mcp_server
```

Open the MCP Inspector at http://127.0.0.1:6274, select `stdio` transport, and connect to the MCP server.

</details>

<details><summary>uv + sse transport</summary>

```bash
# Start the server
uv run -m sitemap_mcp_server

# Start the MCP Inspector in a separate terminal
npx @modelcontextprotocol/inspector connect http://127.0.0.1:8050
```

Open the MCP Inspector at http://127.0.0.1:6274, select `sse` transport, and connect to the MCP server.

</details>

### Claude Desktop

- Make sure you [install the dependencies](#1-install-the-server) first.
- Add this configuration to your [claude_desktop_config.json](https://modelcontextprotocol.io/quickstart/user#2-add-the-filesystem-mcp-server):

```json
{
  "mcpServers": {
    "sitemap": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/sitemap-mcp-server",
        "run",
        "-m",
        "sitemap_mcp_server"
      ],
      "env": { "TRANSPORT": "stdio" }
    }
  }
}
```
- Make sure to update the path to the sitemap-mcp-server directory
- Restart Claude if it's running

### Cursor

<details><summary>stdio transport</summary>

Add this configuration to your Cursor settings:
```json
{
  "mcpServers": {
    "sitemap-uv-local": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/mgo/Documents/coding/mcp/sitemap-mcp-server",
        "run",
        "-m",
        "sitemap_mcp_server"
      ],
      "env": {
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

</details>

<details><summary>sse transport</summary>

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

Start the server
```bash
uv run -m sitemap_mcp_server
```

</details>

### Other MCP Clients

For other MCP clients, use a permutation of the configurations covered above:

- For SSE connections: Use the same approach as the Cursor configuration, adjusting the URL format if needed (some clients require `serverUrl` instead of `url`)
- For stdio connections: Use the uvx approach from the Claude Desktop configuration

Remember that SSE connections require starting the server separately as described in the Cursor section.

## Configuration Options

Customize your server by setting these environment variables:

| Variable | Purpose | Default | Notes |
|----------|---------|--------|--------|
| `TRANSPORT` | Connection method (`sse` or `stdio`) | `sse` | **Critical**: This determines how the server communicates. Set to `stdio` for direct stdio connections, or `sse` for Server-Sent Events. |
| `HOST` | Server address for SSE mode | `0.0.0.0` | Only used when `TRANSPORT=sse` |
| `PORT` | Server port for SSE mode | `8050` | Only used when `TRANSPORT=sse` |
| `CACHE_MAX_AGE` | Sitemap cache duration (seconds) | `86400` (1 day) | |
| `LOG_LEVEL` | Log level (INFO, DEBUG, etc.) | `INFO` | |
| `LOG_FILE` | Log file name | `sitemap_server.log` | |

> **Important**: The `TRANSPORT` environment variable controls whether the server runs in SSE or stdio mode. If you're using a custom configuration, make sure to set this appropriately.



## Code Style and Formatting

This project uses [Black](https://black.readthedocs.io/) for code formatting to maintain consistent style across the codebase.

### Running the Formatter

First, make sure you have the development dependencies installed:

```bash
# Install the package with dev dependencies
uv pip install -e ".[dev]"
```

Then format all Python files in the project:

```bash
black .
```

The configuration for Black is defined in `pyproject.toml` with settings like line length (88 characters) and target Python version (3.11).

## Running Tests

For detailed information on the test structure and how to run tests, please refer to the [tests/README.md](tests/README.md) file.

## Contributing

### Contribution Workflow

1. **Fork the Repository**: Create your own fork of the project.
2. **Create a Branch**: Create a branch for your feature or bugfix.
3. **Make Changes**: Implement your changes, following the code style guidelines.
4. **Run Tests**: Ensure all tests pass and add new tests for new functionality.
5. **Format Code**: Run Black to ensure your code follows the project's style.
6. **Submit a Pull Request**: Create a PR with a clear description of your changes.

---

## Build and Publish the Package

To build and publish the sitemap-mcp-server package to PyPI:

### Build the package
```bash
uv run -m build
```
This will generate distribution files in the `dist/` directory.

### Publish to PyPI
```bash
uv run -m twine upload dist/*
```
This will upload the package to PyPI. You may be prompted for your credentials if not configured.

**Note:** Before publishing, update the version in **both** `pyproject.toml` and `src/sitemap_mcp_server/config.py` (the `APP_VERSION` field) to keep them in sync. Also ensure your credentials are set up for PyPI (see [Twine documentation](https://twine.readthedocs.io/en/stable/)).


### Pull Request Guidelines

- Keep changes focused and atomic
- Include tests for new functionality
- Update documentation as needed
- Ensure all tests pass before submitting
- Follow the existing code style

## Need Help?

If you have questions or need help with development, please:

1. Check existing issues on GitHub
2. Open a new issue for bugs or feature requests
3. Ask questions in the project's discussion forum

Thank you for contributing to the Sitemap MCP Server project!



