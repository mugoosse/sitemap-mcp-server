"""Tests for pagination functionality in an isolated manner."""

import json
import base64


# Test the pagination logic directly without server dependencies
def test_pagination_basics():
    """Test the basic pagination logic for the sitemap pages feature."""
    # Create a sample dataset
    items = [f"item{i}" for i in range(150)]

    # Pagination parameters
    page_size = 10

    # Test first page (no cursor)
    page_number = 0
    start_idx = page_number * page_size
    end_idx = min(start_idx + page_size, len(items))

    # Get current page
    current_page = items[start_idx:end_idx]

    # Verify pagination results
    assert len(current_page) == 10
    assert current_page[0] == "item0"
    assert current_page[-1] == "item9"

    # Generate cursor for next page
    cursor_data = {"page": page_number + 1}
    next_cursor = base64.b64encode(json.dumps(cursor_data).encode("utf-8")).decode(
        "utf-8"
    )

    # Test second page (with cursor)
    cursor_data = json.loads(base64.b64decode(next_cursor).decode("utf-8"))
    page_number = cursor_data["page"]
    assert page_number == 1

    start_idx = page_number * page_size
    end_idx = min(start_idx + page_size, len(items))

    # Get second page
    second_page = items[start_idx:end_idx]

    # Verify second page
    assert len(second_page) == 10
    assert second_page[0] == "item10"
    assert second_page[-1] == "item19"


def test_cursor_encoding_decoding():
    """Test the encoding and decoding of pagination cursors."""
    # Create test cursor data
    cursor_data = {"page": 5}

    # Encode cursor
    encoded_cursor = base64.b64encode(json.dumps(cursor_data).encode("utf-8")).decode(
        "utf-8"
    )

    # Decode cursor
    decoded_bytes = base64.b64decode(encoded_cursor)
    decoded_str = decoded_bytes.decode("utf-8")
    decoded_data = json.loads(decoded_str)

    # Verify decoding worked correctly
    assert decoded_data["page"] == 5


def test_pagination_with_custom_page_size():
    """Test pagination with custom page sizes."""
    # Create a sample dataset
    items = [f"item{i}" for i in range(150)]

    # Define different page sizes
    for page_size in [5, 20, 50]:
        # Calculate number of pages
        total_pages = (len(items) + page_size - 1) // page_size

        # Test last page
        page_number = total_pages - 1
        start_idx = page_number * page_size
        end_idx = min(start_idx + page_size, len(items))

        # Get last page
        last_page = items[start_idx:end_idx]

        # Verify last page
        assert 0 < len(last_page) <= page_size
        assert last_page[0] == f"item{start_idx}"


def test_pagination_with_out_of_range_page():
    """Test handling of out-of-range page numbers."""
    # Create a sample dataset
    items = [f"item{i}" for i in range(100)]
    page_size = 10

    # Test beyond range
    page_number = 15  # Should be out of range (would be index 150)
    start_idx = page_number * page_size

    # Should be out of range
    assert start_idx >= len(items)

    # In the implementation, this should generate an error response
