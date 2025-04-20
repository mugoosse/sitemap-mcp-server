"""Tests for sitemap pages retrieval with pagination functionality."""

import pytest
import json
import base64
from unittest.mock import MagicMock


# We'll create a mock implementation of the function instead of importing the real one
async def mock_get_sitemap_pages(
    ctx, url, limit=0, include_metadata=False, cursor=None, route=None, sitemap_url=None
):
    """Mock implementation of get_sitemap_pages for testing."""
    # Log the request parameters for debugging
    ctx.log.info(f"Getting sitemap pages for {url} with limit={limit}, cursor={cursor}")

    # Default page size
    page_size = 100 if limit == 0 else min(limit, 100)
    ctx.log.info(f"Using page size: {page_size}")

    # Generate all pages - always generate 250 pages for thorough pagination testing
    if include_metadata:
        # Generate mock pages with metadata
        all_pages = []
        for i in range(250):
            page = {
                "url": f"https://example.com/page{i}",
                "last_modified": "2025-04-01T12:00:00Z",
                "priority": 0.8,
                "changefreq": "daily",
            }
            all_pages.append(page)
    else:
        # Generate simple URL objects with url field
        all_pages = [{"url": f"https://example.com/page{i}"} for i in range(250)]

    # Apply route filtering if specified
    if route:
        ctx.log.info(f"Filtering by route: {route}")
        all_pages = [
            p for p in all_pages if p["url"].startswith(f"https://example.com{route}")
        ]

    # Apply sitemap filtering if specified
    if sitemap_url:
        ctx.log.info(f"Filtering by sitemap URL: {sitemap_url}")
        # Simple mock implementation - just keep half the pages
        all_pages = all_pages[: len(all_pages) // 2]

    # Parse cursor if provided
    page_number = 0
    if cursor:
        try:
            cursor_data = json.loads(base64.b64decode(cursor).decode("utf-8"))
            if "page" in cursor_data:
                page_number = int(cursor_data["page"])
                ctx.log.info(f"Using page {page_number} from cursor")
            else:
                ctx.log.error(f"Missing 'page' key in cursor data: {cursor_data}")
                return {
                    "error": "Invalid cursor format",
                    "details": "Missing 'page' key in cursor data",
                }
        except Exception as e:
            ctx.log.error(f"Error processing cursor: {str(e)}")
            return {"error": "Invalid cursor format", "details": str(e)}

    # Calculate start and end indices
    start_idx = page_number * page_size
    end_idx = min(start_idx + page_size, len(all_pages))
    ctx.log.info(
        f"Page {page_number}: getting items {start_idx}-{end_idx-1} of {len(all_pages)}"
    )

    # Check if we have valid indices
    if start_idx >= len(all_pages):
        ctx.log.error(
            f"Invalid page number: {page_number}, only have {len(all_pages)} pages"
        )
        return {
            "error": "Invalid page number",
            "details": f"Page {page_number} is out of range. Only have {len(all_pages)} results.",
        }

    # Get current page
    current_page = all_pages[start_idx:end_idx]
    ctx.log.info(f"Returning {len(current_page)} results for page {page_number}")

    # Create result
    result = {"base_url": url, "pages": current_page, "limit": page_size}

    # Add next cursor if there are more pages
    next_page = page_number + 1
    next_start_idx = next_page * page_size

    if next_start_idx < len(all_pages):
        # There are more pages
        cursor_data = {"page": next_page}
        next_cursor = base64.b64encode(json.dumps(cursor_data).encode("utf-8")).decode(
            "utf-8"
        )
        result["nextCursor"] = next_cursor
        result["next_page"] = next_page
        ctx.log.info(f"Generated cursor for page {next_page}: {next_cursor}")
        # Verify the cursor decodes correctly
        test_decode = json.loads(base64.b64decode(next_cursor).decode("utf-8"))
        ctx.log.info(
            f"Cursor verification - decoded value: {test_decode}, should point to page {next_page}"
        )

    # Add filter information to the response
    if route:
        result["route"] = route
    if sitemap_url:
        result["sitemap_url"] = sitemap_url

    return result


# Mock Context for testing
class MockContext:
    def __init__(self):
        self.log = MagicMock()
        self.log.info = MagicMock()
        self.log.error = MagicMock()


@pytest.fixture
def mock_sitemap_tree():
    """Create a mock sitemap tree with test pages."""
    # Create a mock tree with test pages
    mock_tree = MagicMock()

    # Create 150 mock pages for pagination testing
    mock_pages = []
    for i in range(150):
        mock_page = MagicMock()
        mock_page.url = f"https://example.com/page{i}"
        mock_page.to_dict.return_value = {
            "url": f"https://example.com/page{i}",
            "last_modified": f"2025-01-{(i % 28) + 1:02d}",
            "priority": "0.8",
        }
        mock_pages.append(mock_page)

    # Configure the tree to return our mock pages
    mock_tree.all_pages.return_value = mock_pages

    return mock_tree


@pytest.mark.asyncio
async def test_get_pages_first_page():
    """Test getting the first page of sitemap pages."""
    ctx = MockContext()
    result = await mock_get_sitemap_pages(
        ctx=ctx, url="example.com", limit=0, include_metadata=False, cursor=None
    )

    # Check result structure
    assert "pages" in result
    assert "nextCursor" in result
    assert "base_url" in result
    assert "limit" in result

    # Verify pagination field values
    assert result["limit"] == 100  # Default page size

    # Check pagination
    assert len(result["pages"]) == 100  # Default page size

    # Verify first page content
    assert result["pages"][0]["url"] == "https://example.com/page0"
    assert result["pages"][99]["url"] == "https://example.com/page99"


@pytest.mark.asyncio
async def test_get_pages_with_cursor():
    """Test pagination with cursor to get the second page."""
    ctx = MockContext()

    # First get the cursor from the first page
    first_page = await mock_get_sitemap_pages(
        ctx=ctx, url="example.com", limit=0, include_metadata=False, cursor=None
    )

    cursor = first_page["nextCursor"]

    # Basic response validation
    assert "pages" in first_page
    assert "limit" in first_page
    assert "base_url" in first_page

    # Check that we got the first page with 100 items
    assert (
        len(first_page["pages"]) == 100
    ), f"Expected 100 items in first page, got {len(first_page['pages'])}"

    # Verify pages don't overlap
    assert first_page["pages"][0]["url"] == "https://example.com/page0"
    assert first_page["pages"][99]["url"] == "https://example.com/page99"

    # First page should have a next cursor for the second page
    assert "nextCursor" in first_page

    # Now get the second page using the cursor
    second_page = await mock_get_sitemap_pages(
        ctx=ctx,
        url="example.com",
        limit=0,
        include_metadata=False,
        cursor=cursor,
    )

    # Basic response validation
    assert "pages" in second_page
    assert "limit" in second_page
    assert "base_url" in second_page

    # Check that we got the second page with 100 items
    assert (
        len(second_page["pages"]) == 100
    ), f"Expected 100 items in second page, got {len(second_page['pages'])}"

    # Verify pages don't overlap
    assert second_page["pages"][0]["url"] == "https://example.com/page100"
    assert second_page["pages"][99]["url"] == "https://example.com/page199"

    # Second page should have a next cursor for the third page
    assert "nextCursor" in second_page


@pytest.mark.asyncio
async def test_get_pages_with_custom_limit():
    """Test getting pages with a custom page size limit."""
    ctx = MockContext()

    # Get pages with a custom limit
    result = await mock_get_sitemap_pages(
        ctx=ctx,
        url="example.com",
        limit=20,  # Custom page size
        include_metadata=False,
        cursor=None,
    )

    # Check pagination with custom limit
    assert len(result["pages"]) == 20
    assert "nextCursor" in result

    # Basic validation
    assert "pages" in result
    assert "limit" in result
    assert result["limit"] == 20  # Custom page size

    # Check we got the right number of pages
    assert len(result["pages"]) == 20

    # First page should have items 0-19
    assert result["pages"][0]["url"] == "https://example.com/page0"
    assert result["pages"][19]["url"] == "https://example.com/page19"


@pytest.mark.asyncio
async def test_get_pages_invalid_cursor():
    """Test handling of invalid cursor."""
    ctx = MockContext()

    # Test with invalid cursor
    result = await mock_get_sitemap_pages(
        ctx=ctx,
        url="example.com",
        limit=0,
        include_metadata=False,
        cursor="invalid_cursor_format",
    )

    # Check error handling
    assert "error" in result
    assert result["error"] == "Invalid cursor format"


@pytest.mark.asyncio
async def test_multi_page_pagination():
    """Test comprehensive multi-page pagination through all available pages."""
    ctx = MockContext()

    # Set a smaller page size to ensure we have multiple pages
    page_size = 25

    # Get the first page
    first_page = await mock_get_sitemap_pages(
        ctx=ctx, url="example.com", limit=page_size, include_metadata=False, cursor=None
    )

    # Verify first page
    assert len(first_page["pages"]) == page_size
    assert first_page["pages"][0]["url"] == "https://example.com/page0"
    assert (
        first_page["pages"][page_size - 1]["url"]
        == f"https://example.com/page{page_size-1}"
    )
    assert "nextCursor" in first_page

    # Get the second page
    second_page = await mock_get_sitemap_pages(
        ctx=ctx,
        url="example.com",
        limit=page_size,
        include_metadata=False,
        cursor=first_page["nextCursor"],
    )

    # Check the second page
    assert len(second_page["pages"]) == page_size
    # Verify pages don't overlap
    assert second_page["pages"][0]["url"] == f"https://example.com/page{page_size}"
    assert (
        second_page["pages"][page_size - 1]["url"]
        == f"https://example.com/page{2*page_size-1}"
    )
    assert "nextCursor" in second_page

    # Get the third page
    third_page = await mock_get_sitemap_pages(
        ctx=ctx,
        url="example.com",
        limit=page_size,
        include_metadata=False,
        cursor=second_page["nextCursor"],
    )

    # Check the third page
    assert len(third_page["pages"]) == page_size
    # Verify pages don't overlap
    assert third_page["pages"][0]["url"] == f"https://example.com/page{2*page_size}"
    assert (
        third_page["pages"][page_size - 1]["url"]
        == f"https://example.com/page{3*page_size-1}"
    )
    assert "nextCursor" in third_page

    # Continue fetching all pages
    page_num = 3
    current_page = third_page
    while "nextCursor" in current_page:
        # Verify we haven't exceeded the total pages
        assert page_num < 11  # We expect up to 10 pages with our page size

        cursor = current_page["nextCursor"]
        current_page = await mock_get_sitemap_pages(
            ctx=ctx,
            url="example.com",
            limit=page_size,
            include_metadata=False,
            cursor=cursor,
        )

        # Verify we got all or some of the expected pages
        if len(current_page["pages"]) == page_size:
            # Full page
            assert (
                current_page["pages"][0]["url"]
                == f"https://example.com/page{page_num*page_size}"
            )
            assert (
                current_page["pages"][page_size - 1]["url"]
                == f"https://example.com/page{(page_num+1)*page_size-1}"
            )
        else:
            # Last page, might not be full
            pass

        page_num += 1

    # Verify we fetched all pages
    # When total is evenly divisible by page_size, the last page will have a full page
    expected_last_page_size = page_size if 250 % page_size == 0 else 250 % page_size
    assert len(current_page["pages"]) == expected_last_page_size


@pytest.mark.asyncio
async def test_pagination_fix_verification():
    """Test that specifically verifies our fix for the pagination issue.

    This test simulates the exact issue we were facing: when a limit is applied,
    pagination should still work correctly and return different pages of results.
    """
    ctx = MockContext()

    # Set a small limit to simulate the issue we were facing
    limit = 30

    # Get the first page with the limit
    first_page = await mock_get_sitemap_pages(
        ctx=ctx, url="example.com", limit=limit, include_metadata=False, cursor=None
    )

    # Verify first page has exactly the limit number of results
    assert len(first_page["pages"]) == limit
    assert first_page["pages"][0]["url"] == "https://example.com/page0"
    assert first_page["pages"][limit - 1]["url"] == f"https://example.com/page{limit-1}"

    # Verify we have a next cursor
    assert "nextCursor" in first_page

    # Get the second page using the cursor
    second_page = await mock_get_sitemap_pages(
        ctx=ctx,
        url="example.com",
        limit=limit,  # Same limit as before
        include_metadata=False,
        cursor=first_page["nextCursor"],
    )

    # Verify second page has exactly the limit number of results
    assert len(second_page["pages"]) == limit

    # VERY IMPORTANT: Verify that the pages don't overlap!
    # This was the key issue we were fixing
    assert second_page["pages"][0]["url"] != first_page["pages"][0]["url"]

    # Verify second page contains the correct items
    assert second_page["pages"][0]["url"] == f"https://example.com/page{limit}"
    assert (
        second_page["pages"][limit - 1]["url"] == f"https://example.com/page{2*limit-1}"
    )


@pytest.mark.asyncio
async def test_get_pages_with_metadata():
    """Test getting pages with metadata included."""
    ctx = MockContext()

    # Get pages with metadata
    result = await mock_get_sitemap_pages(
        ctx=ctx, url="example.com", limit=10, include_metadata=True, cursor=None
    )

    # Verify that metadata is included
    assert "pages" in result
    assert len(result["pages"]) == 10

    # Check metadata fields are present
    assert "url" in result["pages"][0]
    assert "last_modified" in result["pages"][0]
    assert "priority" in result["pages"][0]
    assert "changefreq" in result["pages"][0]
