"""
Sitemap MCP Server Configuration
===============================

This module contains the configuration settings for the Sitemap MCP server.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    """Settings for the Sitemap MCP server."""

    APP_NAME: str = "sitemap-mcp-server"
    APP_VERSION: str = "0.1.3"
    APP_DESCRIPTION: str = (
        "MCP server for fetching, parsing and analyzing sitemaps of websites"
    )
    DEPENDENCIES: list[str] = ["mcp[cli]", "pydantic", "ultimate-sitemap-parser"]
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8050"))
    CACHE_MAX_AGE: int = int(os.getenv("CACHE_MAX_AGE", "86400"))
    TRANSPORT: str = os.getenv("TRANSPORT", "sse")
    # LOG_FILE can be set to a writable path, or disabled by setting to "" or None
    LOG_FILE: str | None = os.getenv("LOG_FILE", "sitemap_server.log") or None
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    APP_INSTRUCTIONS: str = """This MCP server provides tools for analyzing website sitemaps.

# Getting Started
1. Use `get_sitemap_tree` to fetch the basic structure of a website's sitemap
2. Use `get_sitemap_pages` to retrieve all pages from a sitemap with filtering options
3. Use `get_sitemap_stats` for comprehensive statistics about a sitemap
4. Use `parse_sitemap_content` to parse raw sitemap XML content

All tools return JSON strings that can be parsed for further processing.
"""


# Create a settings instance for importing elsewhere
settings = Settings()

import logging


def configure_logger():
    """Configure and return the application logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("sitemap-mcp-server")
    # Try to add a file handler if LOG_FILE is set
    if settings.LOG_FILE:
        try:
            file_handler = logging.FileHandler(settings.LOG_FILE)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not set up file logging to {settings.LOG_FILE}: {e}\nFalling back to console logging only.")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
    return logger


logger = configure_logger()
