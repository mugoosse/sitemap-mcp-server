"""
Sitemap MCP Server Prompts
=========================

This module exports the prompts and handlers used by the Sitemap MCP server.
"""

from .prompt_definitions import (
    analyze_sitemap,
    sitemap_health_check,
    extract_sitemap_urls,
    sitemap_missing_analysis,
    visualize_sitemap,
)

__all__ = [
    "analyze_sitemap",
    "sitemap_health_check",
    "extract_sitemap_urls",
    "sitemap_missing_analysis",
    "visualize_sitemap",
]
