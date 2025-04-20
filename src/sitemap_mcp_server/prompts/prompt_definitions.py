"""
Sitemap MCP Server Prompt Definitions
===================================

This module contains the prompt definitions used by the Sitemap MCP server.
"""

from typing import List, Optional
import re
from mcp.server.fastmcp.prompts import base
from ..utils import normalize_and_validate_url


def safe_input(text: str, is_url: bool = False, is_route: bool = False) -> str:
    """
    Sanitize and validate user input based on its type.

    Args:
        text: The input text to sanitize
        is_url: Whether the input is a URL that should be validated
        is_route: Whether the input is a route path that should be validated

    Returns:
        Sanitized and validated input, or None if validation fails
    """
    # Basic sanitization for all inputs
    # Limit length
    if len(text) > 1000:
        text = text[:1000]

    # Remove control characters
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)

    # Escape curly braces to prevent f-string injection
    text = text.replace("{", "{{").replace("}", "}}")

    # URL validation and normalization
    if is_url:
        normalized_url = normalize_and_validate_url(text)
        if not normalized_url:
            return None
        text = normalized_url

    # Route path validation
    if is_route:
        # Ensure route starts with a slash
        if not text.startswith("/"):
            text = "/" + text

        # Remove any query parameters or fragments
        text = text.split("?")[0].split("#")[0]

        # Ensure route only contains valid characters
        if not re.match(r"^[\w\-/]+$", text):
            return None

    return text


def analyze_sitemap(url: str) -> str:
    """
    Prompt for analyzing a website's sitemap structure.

    Args:
        url: The URL of the website to analyze

    Returns:
        A prompt string for sitemap analysis
    """
    safe_url = safe_input(url, is_url=True)
    if not safe_url:
        return "Error: Please provide a valid HTTP or HTTPS URL."

    return f"""Analyze the sitemap structure for {safe_url}.
Please provide a comprehensive analysis of the sitemap hierarchy, page distribution, and content organization.
Include detailed statistics about the sitemap structure, such as page counts, depth distribution, and content types.

If you need to examine specific subsitemaps, you can use the sitemap_url parameter in get_sitemap_pages to filter pages from a specific subsitemap.
"""


def sitemap_health_check(url: str) -> List[base.Message]:
    """
    Prompt for checking the health and SEO aspects of a sitemap.

    Args:
        url: The URL of the website to check

    Returns:
        A conversation for sitemap health checking
    """
    safe_url = safe_input(url, is_url=True)
    if not safe_url:
        return [
            base.AssistantMessage("Error: Please provide a valid HTTP or HTTPS URL.")
        ]

    return [
        # System message replaced with initial assistant message
        base.AssistantMessage(
            "I'll analyze the sitemap as an SEO expert specializing in sitemap analysis."
        ),
        base.UserMessage(
            f"""Please perform a thorough SEO health check on the sitemap for {safe_url}.
Focus on:
1. Sitemap structure and organization
2. Coverage (are important pages included?)
3. Last-modified timestamps and freshness
4. Priority settings
5. Common SEO problems in the sitemap
6. Recommendations for improvement

Start by explaining what you'll do, then use get_sitemap_stats to analyze the sitemap and get_sitemap_pages to examine specific pages."""
        ),
    ]


def extract_sitemap_urls(
    url: str, sitemap_url: Optional[str] = None, route: Optional[str] = None
) -> List[base.Message]:
    """
    Prompt for extracting specific URLs from a sitemap.

    Args:
        url: The website URL
        sitemap_url: Optional specific subsitemap URL to extract URLs from
        route: Optional route path to filter URLs by

    Returns:
        A prompt string for URL extraction
    """
    safe_url = safe_input(url, is_url=True)
    if not safe_url:
        return [
            base.AssistantMessage("Error: Please provide a valid HTTP or HTTPS URL.")
        ]

    # Validate and sanitize sitemap_url if provided
    safe_sitemap_url = None
    if sitemap_url:
        safe_sitemap_url = safe_input(sitemap_url, is_url=True)

    # Validate and sanitize route if provided
    safe_route = None
    if route:
        safe_route = safe_input(route, is_route=True)

    # Build the filters part of the message
    filters = []
    if safe_sitemap_url:
        filters.append(f"- From the specific subsitemap: {safe_sitemap_url}")
    if safe_route:
        filters.append(f"- Only URLs under the route path: {safe_route}")

    filters_text = (
        "\n".join(filters) if filters else "- No filters applied, extracting all URLs"
    )

    return [
        base.AssistantMessage(
            "I'll help you extract and analyze URLs from the sitemap."
        ),
        base.UserMessage(
            f"""Extract URLs from the sitemap for {safe_url} with the following filters:
{filters_text}

Please:
1. Get the pages from the sitemap using get_sitemap_pages
2. Organize and categorize the URLs
3. Identify patterns and URL structures
4. Note any unusual or out-of-place URLs"""
        ),
    ]


def sitemap_missing_analysis(url: str) -> List[base.Message]:
    """
    Prompt for analyzing what content might be missing from a sitemap.

    Args:
        url: The website URL

    Returns:
        A conversation for missing content analysis
    """
    safe_url = safe_input(url, is_url=True)
    if not safe_url:
        return [
            base.AssistantMessage("Error: Please provide a valid HTTP or HTTPS URL.")
        ]

    return [
        base.AssistantMessage(
            "I'll analyze potential missing content in the sitemap as an SEO expert."
        ),
        base.UserMessage(
            f"""Analyze the sitemap for {safe_url} to identify what important content might be missing.

Please:
1. First, get an overview of the sitemap using get_sitemap_stats
2. Then look at the actual pages in the sitemap with get_sitemap_pages
3. Based on the structure and organization of the site:
   - Identify potential gaps in content coverage
   - Look for missing sections or expected content types
   - Check for patterns in the URL structure that might indicate missing pages
   - Consider what types of pages should be in the sitemap but might be missing
4. Provide specific recommendations for improving sitemap coverage"""
        ),
    ]


def visualize_sitemap(url: str) -> List[base.Message]:
    """
    Prompt for creating a Mermaid.js diagram visualizing a sitemap structure.

    Args:
        url: The website URL to visualize

    Returns:
        A conversation for creating a Mermaid.js sitemap visualization
    """
    safe_url = safe_input(url, is_url=True)
    if not safe_url:
        return [
            base.AssistantMessage("Error: Please provide a valid HTTP or HTTPS URL.")
        ]

    return [
        base.AssistantMessage("I'll create a visualization of the sitemap structure."),
        base.UserMessage(
            f"""Create a visual representation of the sitemap structure for {safe_url} using Mermaid.js diagram syntax.

Please:
1. Fetch the sitemap structure using get_sitemap_tree
2. Extract key sections and hierarchies
3. Create a Mermaid.js flowchart with a left-to-right (LR) direction for a columnar layout that shows:
   - Main sections of the site
   - Key subsections and their relationships
   - Notable patterns in the content organization
4. Apply this styling:
   - Root/Home node: Cyan (#40E0D0)
   - Main sections (Level 1): Hot pink (#ff3d9a)
   - Subsections (Level 2): Yellow (#ffdd00)
   - Deep pages (Level 3): Green (#00cc66)
   - Missing standard pages: Gray (#cccccc) with dashed connections
5. Use a clean, readable layout that highlights the most important structural elements
6. Add brief explanations of what the diagram shows

IMPORTANT: Create the diagram as an artifact using the 'mermaid' type if possible. If that's not available, provide the complete Mermaid.js code in a code block with the 'mermaid' language specifier.

Example artifact format (if supported):
```
{{"type": "mermaid", "content": "flowchart LR; A-->B; B-->C; C-->D; D-->A;"}}
```

Example code block format (fallback):
```mermaid
flowchart LR;
    A[Root/Home]:::home --> B[Main Section]:::main;
    B --> C[Subsection]:::sub;
    C --> D[Deep Page]:::deep;
    A -.-> E[Missing Page]:::missing;
    
    classDef home fill:#40E0D0;
    classDef main fill:#ff3d9a;
    classDef sub fill:#ffdd00;
    classDef deep fill:#00cc66;
    classDef missing fill:#cccccc,stroke-dasharray: 5 5;
```

Make sure the diagram is clear, well-structured, and accurately represents the sitemap hierarchy."""
        ),
    ]
