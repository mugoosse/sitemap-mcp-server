"""
Sitemap-related prompts for the MCP server.
"""
from prompts import base
from typing import List, Optional
import re
from utils import normalize_and_validate_url


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
    if text is None:
        return None
        
    # Basic sanitization for all inputs
    # Limit length
    if len(text) > 1000:
        text = text[:1000]
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    
    # Escape curly braces to prevent f-string injection
    text = text.replace('{', '{{').replace('}', '}}')
    
    # URL validation and normalization
    if is_url:
        normalized_url = normalize_and_validate_url(text)
        if not normalized_url:
            return None
        text = normalized_url
        
    # Route path validation
    if is_route:
        # Ensure route starts with a slash
        if not text.startswith('/'):
            text = '/' + text
        
        # Remove any query parameters or fragments
        text = text.split('?')[0].split('#')[0]
        
        # Ensure route only contains valid characters
        if not re.match(r'^[\w\-/]+$', text):
            return None
    
    return text


def analyze_sitemap(url: str, include_stats: bool = True) -> str:
    """
    Prompt for analyzing a website's sitemap structure.
    
    Args:
        url: The URL of the website to analyze
        include_stats: Whether to include detailed statistics
        
    Returns:
        A prompt string for sitemap analysis
    """
    safe_url = safe_input(url, is_url=True)
    if not safe_url:
        return "Error: Please provide a valid HTTP or HTTPS URL."
    
    stats_text = ""
    if include_stats:
        stats_text = "\nInclude detailed statistics about the sitemap structure, such as page counts, depth distribution, and content types."
    
    return f"""Analyze the sitemap structure for {safe_url}.
Please provide a comprehensive analysis of the sitemap hierarchy, page distribution, and content organization.{stats_text}

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
        return [base.SystemMessage("Error: Please provide a valid HTTP or HTTPS URL.")]
    
    return [
        base.SystemMessage("You are an SEO expert specializing in sitemap analysis."),
        base.UserMessage(f"I need a health check for the sitemap at {safe_url}"),
        base.AssistantMessage("I'll analyze the sitemap structure and provide a health assessment. What specific aspects are you most concerned about?"),
        base.UserMessage("I'm particularly interested in SEO optimization, crawlability, and any structural issues.")
    ]

def extract_sitemap_urls(url: str, sitemap_url: Optional[str] = None, route: Optional[str] = None) -> str:
    """
    Prompt for extracting specific URLs from a sitemap.
    
    Args:
        url: The website URL
        sitemap_url: Optional specific subsitemap URL to extract URLs from
        route: Optional route path to filter URLs by
        
    Returns:
        A prompt string for URL extraction
    """
    # Validate inputs
    safe_url = safe_input(url, is_url=True)
    if not safe_url:
        return "Error: Please provide a valid HTTP or HTTPS URL."
    
    safe_sitemap_url = safe_input(sitemap_url, is_url=True) if sitemap_url else None
    safe_route = safe_input(route, is_route=True) if route else None
    
    filter_parts = []
    if safe_sitemap_url:
        filter_parts.append(f"from the specific subsitemap '{safe_sitemap_url}'")
    if safe_route:
        filter_parts.append(f"under the route path '{safe_route}'")
    
    filter_text = " " + ", ".join(filter_parts) if filter_parts else ""
    
    return f"""Extract all URLs{filter_text} from the sitemap at {safe_url}.
Please provide the URLs in a clean, structured format suitable for further processing.

You can use the get_sitemap_pages tool with the sitemap_url and/or route parameters to filter the results more precisely.
"""

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
        return [base.SystemMessage("Error: Please provide a valid HTTP or HTTPS URL.")]
    
    return [
        base.SystemMessage("You are a content strategist and SEO expert."),
        base.UserMessage(f"Analyze what content might be missing from the sitemap at {safe_url}"),
        base.AssistantMessage("I'll examine the sitemap structure and identify potential content gaps. What is the primary purpose of this website?"),
        base.UserMessage("It's a business website focused on providing services and information to customers.")
    ]

def visualize_sitemap(url: str) -> List[base.Message]:
    """
    Prompt for creating a Mermaid.js diagram visualizing a sitemap structure.
    
    Args:
        url: The website URL to visualize
        
    Returns:
        A conversation for creating a Mermaid.js sitemap visualization
    """
    
    # Validate URL
    safe_url = safe_input(url, is_url=True)
    if not safe_url:
        return [base.SystemMessage("Error: Please provide a valid HTTP or HTTPS URL.")]
    
    prompt_content = f"""Analyze the sitemap for {safe_url} and create a Mermaid.js diagram visualizing its structure in a columnar layout. Follow these steps:

1. First analyze the sitemap structure using these specific tools:
   - Use get_sitemap_tree to understand the overall structure and hierarchy
   - Use get_sitemap_pages to gather details about pages at different levels
   - Examine main sections, subsections, and content organization patterns
   - Identify any missing standard business website pages

2. Create a Mermaid diagram with these specifications:
   - Use flowchart LR (left to right) direction for columnar layout
   - Organize nodes in columns by hierarchy depth
   - Group related content using subgraphs
   - Use clear, descriptive node labels

3. Apply this styling:
   - Root/Home node: Cyan (#40E0D0)
   - Main sections (Level 1): Hot pink (#ff3d9a)
   - Subsections (Level 2): Yellow (#ffdd00)
   - Deep pages (Level 3): Green (#00cc66)
   - Missing standard pages: Gray (#cccccc) with dashed connections

4. Content organization guidance:
   - Look for standard business pages (About, Contact, Terms, etc.)
   - Show missing standard pages with dashed lines
   - Limit deep pages to representative samples for readability
   - Use clear subgraph labels for content grouping

Submit the visualization as a Mermaid diagram artifact."""

    return [
        base.SystemMessage("You are a sitemap analyst specializing in website structure visualization and information architecture."),
        base.UserMessage(prompt_content)
    ]