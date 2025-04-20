from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dotenv import load_dotenv
import time
import base64
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
from pydantic import Field
from usp.objects.sitemap import AbstractSitemap
from usp.tree import sitemap_tree_for_homepage, sitemap_from_str
from usp.helpers import strip_url_to_homepage
from urllib.parse import urlparse

# Import from our modular structure
from .config import logger
from .utils import CustomJSONEncoder, safe_json_dumps, normalize_and_validate_url
from .prompts import (
    analyze_sitemap,
    sitemap_health_check,
    extract_sitemap_urls,
    sitemap_missing_analysis,
    visualize_sitemap,
)
from .config import settings

load_dotenv()


@dataclass
class SitemapContext:
    """Context for the Sitemap MCP server."""

    # Cache for sitemap trees to avoid repeated fetches
    _sitemap_cache: Dict[str, Tuple[datetime, AbstractSitemap]] = field(
        default_factory=dict
    )

    def get_cached_sitemap(
        self, url: str, max_age_seconds: int = None
    ) -> Optional[AbstractSitemap]:
        """Get a cached sitemap tree if it exists and is not expired.

        Args:
            url: The URL to check in the cache
            max_age_seconds: Maximum age in seconds for the cached entry to be valid

        Returns:
            The cached sitemap tree if found and not expired, None otherwise
        """
        if max_age_seconds is None:
            max_age_seconds = settings.CACHE_MAX_AGE

        # Normalize the URL to its homepage for consistent cache keys
        try:
            homepage_url = strip_url_to_homepage(url)
            logger.debug(f"Normalized URL {url} to homepage {homepage_url}")
        except Exception as e:
            logger.warning(
                f"Failed to normalize URL {url}: {str(e)}. Using original URL as cache key."
            )
            homepage_url = url

        if homepage_url in self._sitemap_cache:
            timestamp, tree = self._sitemap_cache[homepage_url]
            if (datetime.now() - timestamp).total_seconds() < max_age_seconds:
                logger.info(
                    f"Using cached sitemap tree for {url} (cache key: {homepage_url})"
                )
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
            logger.warning(
                f"Failed to normalize URL {url}: {str(e)}. Using original URL as cache key."
            )
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
    settings.APP_NAME,
    version=settings.APP_VERSION,
    dependencies=settings.DEPENDENCIES,
    description=settings.APP_DESCRIPTION,
    instructions=settings.APP_INSTRUCTIONS,
    lifespan=sitemap_lifespan,
    host=settings.HOST,
    port=settings.PORT,
)


@mcp.tool(
    description="Fetch and parse the sitemap tree from a website URL",
)
async def get_sitemap_tree(
    ctx: Context,
    url: str = Field(
        ..., description="The URL of the website homepage (e.g., https://example.com)"
    ),
    include_pages: bool = Field(
        False, description="Whether to include page details in the response"
    ),
) -> str:
    try:
        normalized_url = normalize_and_validate_url(url)
        if not normalized_url:
            return safe_json_dumps(
                {
                    "error": "Invalid URL provided. Please provide a valid HTTP or HTTPS URL.",
                    "type": "ValidationError",
                }
            )
        url = normalized_url
        tree = ctx.request_context.lifespan_context.get_sitemap(url)
        page_count = 0
        sitemap_count = 0
        if hasattr(tree, "all_pages"):
            try:
                page_count = sum(1 for _ in tree.all_pages())
            except Exception as e:
                logger.debug(f"Error counting pages: {str(e)}")
        if hasattr(tree, "all_sitemaps"):
            try:
                sitemap_count = sum(1 for _ in tree.all_sitemaps())
            except Exception as e:
                logger.debug(f"Error counting sitemaps: {str(e)}")
        logger.info(f"Found {page_count} pages and {sitemap_count} sitemaps for {url}.")
        sitemap_dict = tree.to_dict(with_pages=include_pages)
        return safe_json_dumps(sitemap_dict)
    except Exception as e:
        error_msg = f"Error fetching sitemap tree for {url}: {str(e)}"
        logger.error(error_msg)
        logger.exception(f"Detailed exception while fetching sitemap for {url}:")
        return safe_json_dumps(
            {"error": error_msg, "type": e.__class__.__name__, "details": str(e)}
        )


@mcp.tool(
    description="Get all pages from a website's sitemap with optional limits and filtering options. Supports cursor-based pagination.",
)
async def get_sitemap_pages(
    ctx: Context,
    url: str = Field(
        ..., description="The URL of the website homepage (e.g., https://example.com)"
    ),
    limit: int = Field(
        0,
        description="Maximum number of pages to return per page (0 for default of 100)",
    ),
    include_metadata: bool = Field(
        False,
        description="Whether to include additional page metadata (priority, lastmod, etc.)",
    ),
    route: str = Field(
        "", description="Optional route path to filter pages by (e.g., '/blog')"
    ),
    sitemap_url: str = Field(
        "", description="Optional URL of a specific sitemap to get pages from"
    ),
    cursor: str = Field(
        "", description="Pagination cursor for fetching the next page of results"
    ),
) -> str:
    try:
        normalized_url = normalize_and_validate_url(url)
        if not normalized_url:
            return safe_json_dumps(
                {
                    "error": "Invalid URL provided. Please provide a valid HTTP or HTTPS URL.",
                    "type": "ValidationError",
                }
            )
        url = normalized_url
        main_tree = ctx.request_context.lifespan_context.get_sitemap(url)
        target_sitemap = main_tree
        # If filtering by sitemap_url, find the specific sitemap
        if sitemap_url and sitemap_url.strip():
            found = False
            for sitemap in main_tree.all_sitemaps():
                if hasattr(sitemap, "url") and sitemap.url == sitemap_url:
                    target_sitemap = sitemap
                    found = True
                    break
            if not found:
                return safe_json_dumps(
                    {
                        "base_url": url,
                        "sitemap_url": sitemap_url,
                        "pages": [],
                        "warning": f"Sitemap URL {sitemap_url} not found",
                    },
                    cls=CustomJSONEncoder,
                )

        # Collect matching pages
        matching_pages = []

        # Normalize and validate route
        filter_by_route = bool(route and route.strip())
        if filter_by_route:
            # Ensure route starts with / and does not end with / unless it's just "/"
            if not route.startswith("/"):
                route = "/" + route
            if route.endswith("/") and len(route) > 1:
                route = route[:-1]
            parsed_url = urlparse(url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for page in target_sitemap.all_pages():
            if filter_by_route:
                page_url = page.url
                # Allow all if route == "/"
                if route == "/":
                    pass
                else:
                    if not (
                        page_url == base_domain + route
                        or page_url == base_domain + route + "/"
                        or page_url.startswith(base_domain + route + "/")
                    ):
                        continue
            if include_metadata:
                matching_pages.append(page.to_dict())
            else:
                matching_pages.append({"url": page.url})
        # Pagination logic
        total_pages = len(matching_pages)
        page_size = 100 if limit == 0 else min(limit, 100)
        page_number = 0
        if cursor and cursor.strip():
            try:
                cursor_data = json.loads(base64.b64decode(cursor).decode("utf-8"))
                if "page" in cursor_data:
                    page_number = int(cursor_data["page"])
            except Exception:
                pass
        start_idx = page_number * page_size
        end_idx = min(start_idx + page_size, total_pages)
        current_page = matching_pages[start_idx:end_idx]
        # Generate next cursor if there are more pages
        next_page = page_number + 1
        next_start_idx = next_page * page_size
        next_cursor = None
        if next_start_idx < total_pages:
            cursor_data = {"page": next_page}
            next_cursor = base64.b64encode(
                json.dumps(cursor_data).encode("utf-8")
            ).decode("utf-8")
        # Build response
        response = {
            "url": url,
            "page_count": total_pages,
            "pages": current_page,
            "limit": page_size,
        }
        if next_cursor:
            response["nextCursor"] = next_cursor
        return safe_json_dumps(response)

    except Exception as e:
        return safe_json_dumps(
            {
                "error": f"Error fetching sitemap pages for {url}: {str(e)}",
                "type": type(e).__name__,
            }
        )


@mcp.tool(
    description="Get comprehensive statistics about a website's sitemap structure"
)
async def get_sitemap_stats(
    ctx: Context,
    url: str = Field(
        ..., description="The URL of the website homepage (e.g., https://example.com)"
    ),
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
            return safe_json_dumps(
                {
                    "error": "Invalid URL provided. Please provide a valid HTTP or HTTPS URL.",
                    "type": "ValidationError",
                }
            )
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
            sitemap_url = getattr(sitemap, "url", None)
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
            if hasattr(sitemap, "pages"):
                for page in sitemap.pages:
                    # Update subsitemap stats
                    current_sitemap_stats["page_count"] += 1

                    # Collect priority if available
                    if hasattr(page, "priority") and page.priority is not None:
                        try:
                            priority_value = float(page.priority)
                            current_sitemap_stats["priorities"].append(priority_value)
                        except (ValueError, TypeError):
                            pass

                    # Collect last modified date if available
                    if (
                        hasattr(page, "last_modified")
                        and page.last_modified is not None
                    ):
                        current_sitemap_stats["last_modified_dates"].append(
                            page.last_modified.isoformat()
                        )

            # Calculate priority statistics for this sitemap if we have any pages
            if current_sitemap_stats["priorities"]:
                current_sitemap_stats["priority_stats"] = {
                    "min": min(current_sitemap_stats["priorities"]),
                    "max": max(current_sitemap_stats["priorities"]),
                    "avg": sum(current_sitemap_stats["priorities"])
                    / len(current_sitemap_stats["priorities"]),
                }

            # Calculate last modified stats if available
            if current_sitemap_stats["last_modified_dates"]:
                current_sitemap_stats["last_modified_count"] = len(
                    current_sitemap_stats["last_modified_dates"]
                )

            # Remove raw data lists to keep response size reasonable
            del current_sitemap_stats["priorities"]
            del current_sitemap_stats["last_modified_dates"]

            # Add to the list of subsitemap stats
            subsitemap_stats.append(current_sitemap_stats)

        # Collect page statistics for total stats
        for page in tree.all_pages():
            total_stats["page_count"] += 1

            if hasattr(page, "last_modified") and page.last_modified is not None:
                total_stats["last_modified_dates"].append(
                    page.last_modified.isoformat()
                )

            if hasattr(page, "priority") and page.priority is not None:
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
        result = {"total": total_stats, "subsitemaps": subsitemap_stats}

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
    content: str = Field(
        ..., description="The content of the sitemap (XML, text, etc.)"
    ),
    include_pages: bool = Field(
        False, description="Whether to include page details in the response"
    ),
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
@mcp.prompt(
    name="analyze_sitemap",
    description="Analyze a website's sitemap structure and organization",
)
def analyze_sitemap_prompt(
    url: str = Field(..., description="The URL of the website to analyze"),
) -> str:
    logger.info(f"Analyzing sitemap for {url}")
    return analyze_sitemap(url)


@mcp.prompt(
    name="sitemap_health_check",
    description="Check the health and SEO aspects of a website's sitemap",
)
def sitemap_health_check_prompt(
    url: str = Field(..., description="The URL of the website to check")
) -> list[base.Message]:
    logger.info(f"Checking sitemap health for {url}")
    return sitemap_health_check(url)


@mcp.prompt(
    name="extract_sitemap_urls",
    description="Extract and filter specific URLs from a website's sitemap",
)
def extract_sitemap_urls_prompt(
    url: str = Field(..., description="The website URL"),
    sitemap_url: Optional[str] = Field(
        None, description="Optional specific subsitemap URL to extract URLs from"
    ),
    route: Optional[str] = Field(
        None, description="Optional route path to filter URLs by"
    ),
) -> list[base.Message]:
    logger.info(f"Extracting sitemap URLs for {url}")
    return extract_sitemap_urls(url, sitemap_url, route)


@mcp.prompt(
    name="sitemap_missing_analysis",
    description="Analyze what content might be missing from a website's sitemap",
)
def sitemap_missing_analysis_prompt(
    url: str = Field(..., description="The URL of the website to analyze")
) -> list[base.Message]:
    logger.info(f"Analyzing missing content for {url}")
    return sitemap_missing_analysis(url)


@mcp.prompt(
    name="visualize_sitemap", description="Visualize a sitemap as a Mermaid.js diagram"
)
def visualize_sitemap_prompt(
    url: str = Field(..., description="The URL of the website to visualize")
) -> list[base.Message]:
    logger.info(f"Visualizing sitemap for {url}")
    return visualize_sitemap(url)


async def main():
    transport = settings.TRANSPORT
    if transport == "sse":
        await mcp.run_sse_async()
    else:
        await mcp.run_stdio_async()
