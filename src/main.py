from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dotenv import load_dotenv
import asyncio
import json
import os
import re
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
from pydantic import Field
from usp.objects.sitemap import AbstractSitemap
from usp.tree import sitemap_tree_for_homepage, sitemap_from_str
from usp.helpers import strip_url_to_homepage
from prompts import sitemap_prompts
from logger import logger
from utils import CustomJSONEncoder, safe_json_dumps, normalize_and_validate_url

load_dotenv()

CACHE_MAX_AGE = int(os.getenv("CACHE_MAX_AGE", "86400"))

@dataclass
class SitemapContext:
    """Context for the Sitemap MCP server."""
    # Cache for sitemap trees to avoid repeated fetches
    _sitemap_cache: Dict[str, Tuple[datetime, AbstractSitemap]] = field(default_factory=dict)
    
    def get_cached_sitemap(self, url: str, max_age_seconds: int = None) -> Optional[AbstractSitemap]:
        """Get a cached sitemap tree if it exists and is not expired.
        
        Args:
            url: The URL to check in the cache
            max_age_seconds: Maximum age in seconds for the cached entry to be valid
            
        Returns:
            The cached sitemap tree if found and not expired, None otherwise
        """
        if max_age_seconds is None:
            max_age_seconds = CACHE_MAX_AGE
            
        # Normalize the URL to its homepage for consistent cache keys
        try:
            homepage_url = strip_url_to_homepage(url)
            logger.debug(f"Normalized URL {url} to homepage {homepage_url}")
        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {str(e)}. Using original URL as cache key.")
            homepage_url = url
            
        if homepage_url in self._sitemap_cache:
            timestamp, tree = self._sitemap_cache[homepage_url]
            if (datetime.now() - timestamp).total_seconds() < max_age_seconds:
                logger.info(f"Using cached sitemap tree for {url} (cache key: {homepage_url})")
                return tree
        return None
    
    def cache_sitemap(self, url: str, tree: AbstractSitemap) -> None:
        """Cache a sitemap tree for a URL.
        
        Args:
            url: The URL to cache the sitemap for
            tree: The sitemap tree to cache
        """
        # Normalize the URL to its homepage for consistent cache keys
        try:
            homepage_url = strip_url_to_homepage(url)
            logger.debug(f"Normalized URL {url} to homepage {homepage_url} for caching")
        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {str(e)}. Using original URL as cache key.")
            homepage_url = url
            
        self._sitemap_cache[homepage_url] = (datetime.now(), tree)
        logger.info(f"Cached sitemap tree for {url} (cache key: {homepage_url})")
    
    def clear_cache(self) -> None:
        self._sitemap_cache.clear()
        logger.info("Sitemap cache cleared")
        
    def get_sitemap(self, url: str) -> AbstractSitemap:
        """Get a sitemap tree for a homepage URL with caching.
        
        This method first normalizes the URL to its homepage using strip_url_to_homepage
        before checking the cache or fetching a new sitemap. This ensures that different URLs
        pointing to the same website (e.g., https://example.com and https://example.com/blog)
        will use the same cached sitemap data.
        
        Args:
            url: The URL of the website (will be normalized to homepage)
            
        Returns:
            The sitemap tree object
        """
        # Try to get from cache first
        cached_tree = self.get_cached_sitemap(url)
        if cached_tree:
            return cached_tree
        
        logger.info(f"Fetching sitemap tree for {url}")
        start_time = time.time()
        
        # We still use the original URL for fetching, as sitemap_tree_for_homepage
        # will handle the normalization internally
        tree = sitemap_tree_for_homepage(url)
        
        # Cache using the normalized URL
        self.cache_sitemap(url, tree)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Fetched sitemap tree for {url} in {elapsed_time:.2f} seconds")
        
        return tree

@asynccontextmanager
async def sitemap_lifespan(server: FastMCP) -> AsyncIterator[SitemapContext]:
    """
    Manages the Sitemap server lifecycle.

    Args:
        server: The FastMCP server instance

    Yields:
        SitemapContext: The context for the Sitemap server
    """
    context = SitemapContext()
    
    try:
        logger.info("Sitemap server initialized")
        yield context
    finally:
        logger.info("Cleaning up sitemap cache")
        context.clear_cache()

mcp = FastMCP(
    "sitemap",
    description="MCP server for fetching, parsing and analyzing sitemaps of websites",
    instructions="""This MCP server provides tools for analyzing website sitemaps.

# Getting Started
1. Use `get_sitemap_tree` to fetch the basic structure of a website's sitemap
2. Use `get_sitemap_pages` to retrieve all pages from a sitemap with filtering options
3. Use `get_sitemap_stats` for comprehensive statistics about a sitemap
4. Use `parse_sitemap_content` to parse raw sitemap XML content


All tools return JSON strings that can be parsed for further processing.
""",
    lifespan=sitemap_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)        

@mcp.tool(description="Fetch and parse the sitemap tree from a website URL")
async def get_sitemap_tree(
    ctx: Context,
    url: str = Field(..., description="The URL of the website homepage (e.g., https://example.com)"),
    include_pages: bool = Field(False, description="Whether to include page details in the response")
) -> str:
    """Fetch and parse the sitemap tree from a website URL.
    
    Returns a JSON string representing the sitemap tree structure.
    """
    try:
        # Validate URL and normalize it if needed
        normalized_url = normalize_and_validate_url(url)
        if not normalized_url:
            return safe_json_dumps({
                "error": "Invalid URL provided. Please provide a valid HTTP or HTTPS URL.",
                "type": "ValidationError"
            })
        url = normalized_url
        tree = ctx.request_context.lifespan_context.get_sitemap(url)
        
        page_count = 0
        sitemap_count = 0
        
        if hasattr(tree, 'all_pages'):
            try:
                page_count = sum(1 for _ in tree.all_pages())
            except Exception as e:
                logger.debug(f"Error counting pages: {str(e)}")
                
        if hasattr(tree, 'all_sitemaps'):
            try:
                sitemap_count = sum(1 for _ in tree.all_sitemaps())
            except Exception as e:
                logger.debug(f"Error counting sitemaps: {str(e)}")
                
        logger.info(f"Found {page_count} pages and {sitemap_count} sitemaps for {url}.")
        
        return safe_json_dumps(tree.to_dict(with_pages=include_pages))

    except Exception as e:
        error_msg = f"Error fetching sitemap tree for {url}: {str(e)}"
        logger.error(error_msg)
        logger.exception(f"Detailed exception while fetching sitemap for {url}:")
        return safe_json_dumps({
            "error": error_msg, 
            "type": e.__class__.__name__,
            "details": str(e)
        })

@mcp.tool(description="Get all pages from a website's sitemap with optional limits and filtering options")
async def get_sitemap_pages(
    ctx: Context,
    url: str = Field(..., description="The URL of the website homepage (e.g., https://example.com)"),
    limit: int = Field(0, description="Maximum number of pages to return (0 for no limit)"),
    include_metadata: bool = Field(False, description="Whether to include additional page metadata (priority, lastmod, etc.)"),
    route: Optional[str] = Field(None, description="Optional route path to filter pages by (e.g., '/blog')"),
    sitemap_url: Optional[str] = Field(None, description="Optional URL of a specific sitemap to get pages from")
) -> str:
    """Get all pages from a website's sitemap with optional limits and filtering options.
    
    This tool fetches all pages from a website's sitemap and returns them as a list.
    You can limit the number of pages returned and control whether additional page metadata is included.
    
    Filtering options:
    - If a route is specified, only pages that belong to that route will be returned.
      For example, if the route is '/blog', it will return all pages that start with 'https://example.com/blog'.
    - If a sitemap_url is specified, only pages from that specific sitemap will be returned.
      This is useful when you know the URL of a specific subsitemap from a previous get_sitemap_tree or get_sitemap_stats call.
    
    Results are cached to improve performance for repeated requests.
    When include_metadata is True, pages are sorted by most recently updated (newest first).
    """
    try:
        # Validate URL and normalize it if needed
        normalized_url = normalize_and_validate_url(url)
        if not normalized_url:
            return safe_json_dumps({
                "error": "Invalid URL provided. Please provide a valid HTTP or HTTPS URL.",
                "type": "ValidationError"
            })
        url = normalized_url
            
        # Validate and normalize sitemap URL if provided
        if sitemap_url:
            normalized_sitemap_url = normalize_and_validate_url(sitemap_url)
            if not normalized_sitemap_url:
                return safe_json_dumps({
                    "error": "Invalid sitemap URL provided. Please provide a valid HTTP or HTTPS URL.",
                    "type": "ValidationError"
                })
            sitemap_url = normalized_sitemap_url
            
        # Simple route validation
        if route:
            # Ensure route starts with a slash
            if not route.startswith('/'):
                route = '/' + route
        
        # Start timing the operation
        start_time = time.time()
        
        # Check if we need to filter by route
        filter_by_route = route is not None
        filter_by_sitemap = sitemap_url is not None
        
        # Build log message for operation start
        log_parts = [f"Fetching sitemap pages for {url}"]
        
        # Normalize route if needed
        if filter_by_route:
            # Normalize the route (ensure it starts with / and doesn't end with /)
            if not route.startswith('/'):
                route = '/' + route
            if route.endswith('/') and len(route) > 1:
                route = route[:-1]
            log_parts.append(f"with route filter: {route}")
            
            # Extract the base domain from the URL for route filtering
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if filter_by_sitemap:
            log_parts.append(f"with sitemap filter: {sitemap_url}")
            
        if limit > 0:
            log_parts.append(f"(limit: {limit})")
            
        # Log the operation start
        logger.info(" ".join(log_parts))
        
        # Get the main sitemap tree with caching
        main_tree = ctx.request_context.lifespan_context.get_sitemap(url)
        
        # Determine which sitemap to use (main tree or specific subsitemap)
        target_sitemap = main_tree  # Default to the main sitemap tree
        
        # If filtering by sitemap_url, find the specific sitemap
        if filter_by_sitemap:
            found = False
            for sitemap in main_tree.all_sitemaps():
                if hasattr(sitemap, 'url') and sitemap.url == sitemap_url:
                    target_sitemap = sitemap
                    found = True
                    break
                    
            if not found:
                logger.warning(f"Sitemap URL {sitemap_url} not found in the sitemap tree for {url}")
                # Return empty result with appropriate message
                return safe_json_dumps({
                    "base_url": url,
                    "sitemap_url": sitemap_url,
                    "matching_pages": [],
                    "total_matching_pages": 0,
                    "warning": f"Sitemap URL {sitemap_url} not found"
                }, cls=CustomJSONEncoder)
        
        # Collect matching pages
        matching_pages = []
        
        # Process pages from the target sitemap
        for page in target_sitemap.all_pages():
            # Apply route filter if specified
            if filter_by_route:
                page_url = page.url
                # Check if the page URL belongs to the specified route
                if not (page_url.startswith(base_domain + route) and 
                        (page_url == base_domain + route or 
                         page_url == base_domain + route + '/' or 
                         page_url.startswith(base_domain + route + '/') or 
                         route == '/')):
                    # Skip pages that don't match the route
                    continue
            
            # Add the page to our results
            if include_metadata:
                matching_pages.append(page.to_dict())
            else:
                matching_pages.append({"url": page.url})
                
            # Check if we've reached the limit
            if limit > 0 and len(matching_pages) >= limit:
                break
        
        # Sort the pages by last_modified in descending order (newest first) if metadata is included
        if include_metadata:
            # Define a key function that handles None values for sorting
            def sort_key(page):
                return (page.get('last_modified') is not None, page.get('last_modified', ''))  # Tuple: (has_date, date)
                
            # Apply sorting
            matching_pages.sort(key=sort_key, reverse=True)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Build response data
        response_data = {
            "base_url": url,
            "matching_pages": matching_pages,
            "total_matching_pages": len(matching_pages)
        }
        
        # Add filter information to the response
        if filter_by_route:
            response_data["route"] = route
        if filter_by_sitemap:
            response_data["sitemap_url"] = sitemap_url
        
        # Build log message for operation completion
        log_message = f"Fetched {len(matching_pages)} sitemap pages for {url}"
        if filter_by_route:
            log_message += f" with route '{route}'"
        if filter_by_sitemap:
            log_message += f" with sitemap URL '{sitemap_url}'"
        log_message += f" in {elapsed_time:.2f} seconds"
        if include_metadata:
            log_message += " (sorted by most recently updated)"
        logger.info(log_message)
        
        # Return the result
        return safe_json_dumps(response_data)
    except Exception as e:
        # Build error message with filter info
        filter_info = ""
        if route:
            filter_info += f" with route '{route}'"
        if sitemap_url:
            filter_info += f" with sitemap URL '{sitemap_url}'"
            
        error_msg = f"Error fetching sitemap pages for {url}{filter_info}: {str(e)}"
        logger.error(error_msg)
        logger.exception(f"Detailed exception while fetching sitemap pages for {url}:")
        return safe_json_dumps({
            "error": error_msg,
            "type": e.__class__.__name__,
            "details": str(e)
        })

@mcp.tool(description="Get comprehensive statistics about a website's sitemap structure")
async def get_sitemap_stats(
    ctx: Context,
    url: str = Field(..., description="The URL of the website homepage (e.g., https://example.com)")
) -> str:
    """Get statistics about a website's sitemap.
    
    This tool analyzes a website's sitemap and returns statistics such as:
    - Total number of pages
    - Number of subsitemaps
    - Types of sitemaps found
    - Last modification dates (min, max, average)
    - Priority statistics
    - Detailed statistics for each subsitemap
    """
    try:
        # Validate URL and normalize it if needed
        normalized_url = normalize_and_validate_url(url)
        if not normalized_url:
            return safe_json_dumps({
                "error": "Invalid URL provided. Please provide a valid HTTP or HTTPS URL.",
                "type": "ValidationError"
            })
        url = normalized_url
        # Log the operation start
        logger.info(f"Analyzing sitemap statistics for {url}")
        start_time = time.time()
        
        # Get the sitemap tree with caching directly from the context
        tree = ctx.request_context.lifespan_context.get_sitemap(url)
        
        # Collect total statistics
        total_stats = {
            "url": url,
            "page_count": 0,
            "sitemap_count": 0,
            "sitemap_types": set(),
            "last_modified_dates": [],
            "priorities": [],
        }
        
        # Dictionary to store stats for each subsitemap
        subsitemap_stats = []
        
        # Process each sitemap and collect stats
        for sitemap in tree.all_sitemaps():
            # Update total stats
            total_stats["sitemap_count"] += 1
            total_stats["sitemap_types"].add(sitemap.__class__.__name__)
            
            # Create individual sitemap stats
            sitemap_url = getattr(sitemap, 'url', None)
            if not sitemap_url:
                continue
                
            # Initialize stats for this subsitemap
            current_sitemap_stats = {
                "url": sitemap_url,
                "type": sitemap.__class__.__name__,
                "page_count": 0,
                "priorities": [],
                "last_modified_dates": [],
            }
            
            # Count pages in this sitemap
            if hasattr(sitemap, 'pages'):
                for page in sitemap.pages:
                    # Update subsitemap stats
                    current_sitemap_stats["page_count"] += 1
                    
                    # Collect priority if available
                    if hasattr(page, 'priority') and page.priority is not None:
                        try:
                            priority_value = float(page.priority)
                            current_sitemap_stats["priorities"].append(priority_value)
                        except (ValueError, TypeError):
                            pass
                    
                    # Collect last modified date if available
                    if hasattr(page, 'last_modified') and page.last_modified is not None:
                        current_sitemap_stats["last_modified_dates"].append(page.last_modified.isoformat())
            
            # Calculate priority statistics for this sitemap if we have any pages
            if current_sitemap_stats["priorities"]:
                current_sitemap_stats["priority_stats"] = {
                    "min": min(current_sitemap_stats["priorities"]),
                    "max": max(current_sitemap_stats["priorities"]),
                    "avg": sum(current_sitemap_stats["priorities"]) / len(current_sitemap_stats["priorities"]),
                }
            
            # Calculate last modified stats if available
            if current_sitemap_stats["last_modified_dates"]:
                current_sitemap_stats["last_modified_count"] = len(current_sitemap_stats["last_modified_dates"])
            
            # Remove raw data lists to keep response size reasonable
            del current_sitemap_stats["priorities"]
            del current_sitemap_stats["last_modified_dates"]
            
            # Add to the list of subsitemap stats
            subsitemap_stats.append(current_sitemap_stats)
        
        # Collect page statistics for total stats
        for page in tree.all_pages():
            total_stats["page_count"] += 1
            
            if hasattr(page, 'last_modified') and page.last_modified is not None:
                total_stats["last_modified_dates"].append(page.last_modified.isoformat())
            
            if hasattr(page, 'priority') and page.priority is not None:
                try:
                    total_stats["priorities"].append(float(page.priority))
                except (ValueError, TypeError):
                    pass
        
        # Calculate priority statistics for total stats if we have any pages
        if total_stats["priorities"]:
            total_stats["priority_stats"] = {
                "min": min(total_stats["priorities"]),
                "max": max(total_stats["priorities"]),
                "avg": sum(total_stats["priorities"]) / len(total_stats["priorities"]),
            }
        
        # Calculate last modified stats for total if available
        if total_stats["last_modified_dates"]:
            total_stats["last_modified_count"] = len(total_stats["last_modified_dates"])
        
        # Convert set to list for JSON serialization
        total_stats["sitemap_types"] = list(total_stats["sitemap_types"])
        
        # Remove the raw data lists to keep response size reasonable
        del total_stats["last_modified_dates"]
        del total_stats["priorities"]
        
        # Combine total and subsitemap stats
        result = {
            "total": total_stats,
            "subsitemaps": subsitemap_stats
        }
        
        # Log the operation completion
        elapsed_time = time.time() - start_time
        logger.info(f"Analyzed sitemap stats for {url} in {elapsed_time:.2f} seconds")
        
        # Return as JSON
        return safe_json_dumps(result)
    except Exception as e:
        error_msg = f"Error analyzing sitemap for {url}: {str(e)}"
        logger.error(error_msg)
        logger.exception(f"Detailed exception while analyzing sitemap for {url}:")
        return safe_json_dumps({"error": error_msg})

@mcp.tool(description="Parse a sitemap directly from its XML or text content")
async def parse_sitemap_content(
    ctx: Context,
    content: str = Field(..., description="The content of the sitemap (XML, text, etc.)"),
    include_pages: bool = Field(False, description="Whether to include page details in the response")
) -> str:
    """Parse a sitemap from its content.
    
    This tool parses a sitemap directly from its XML or text content and returns a structured representation.
    """
    try:
        logger.info("Parsing sitemap from content")
        
        parsed_sitemap = sitemap_from_str(content)
        
        return safe_json_dumps(parsed_sitemap.to_dict(with_pages=include_pages))
    except Exception as e:
        error_msg = f"Error parsing sitemap content: {str(e)}"
        logger.error(error_msg)
        return safe_json_dumps({"error": error_msg})

# Register prompts
@mcp.prompt(description="Analyze a website's sitemap structure and organization")
def analyze_sitemap(
    url: str = Field(..., description="The URL of the website to analyze"),
    include_stats: bool = Field(True, description="Whether to include detailed statistics")
) -> str:
    """Analyze a website's sitemap structure and organization."""
    return sitemap_prompts.analyze_sitemap(url, include_stats)

@mcp.prompt(description="Check the health and SEO aspects of a website's sitemap")
def sitemap_health_check(
    url: str = Field(..., description="The URL of the website to check")
) -> list[base.Message]:
    """Check the health and SEO aspects of a website's sitemap."""
    return sitemap_prompts.sitemap_health_check(url)

@mcp.prompt(description="Extract and filter specific URLs from a website's sitemap")
def extract_sitemap_urls(
    url: str = Field(..., description="The website URL"),
    sitemap_url: Optional[str] = Field(None, description="Optional specific subsitemap URL to extract URLs from"),
    route: Optional[str] = Field(None, description="Optional route path to filter URLs by")
) -> str:
    """Extract and filter specific URLs from a website's sitemap."""
    return sitemap_prompts.extract_sitemap_urls(url, sitemap_url, route)

@mcp.prompt(description="Analyze what content might be missing from a website's sitemap")
def sitemap_missing_analysis(
    url: str = Field(..., description="The URL of the website to analyze")
) -> list[base.Message]:
    """Analyze what content might be missing from a website's sitemap."""
    return sitemap_prompts.sitemap_missing_analysis(url)

@mcp.prompt(description="Visualize a sitemap as a Mermaid.js diagram")
def visualize_sitemap(
    url: str = Field(..., description="The URL of the website to visualize")
) -> list[base.Message]:
    """Visualize a sitemap as a Mermaid.js diagram."""
    return sitemap_prompts.visualize_sitemap(url)

async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        await mcp.run_sse_async()
    else:
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())