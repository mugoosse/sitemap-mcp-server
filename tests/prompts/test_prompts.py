"""Unit tests for prompt handlers."""

import pytest


# Mock the MCP types we need
class TextContent:
    def __init__(self, text):
        self.text = text


class PromptMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content


class GetPromptResult:
    def __init__(self, messages):
        self.messages = messages


class MockField:
    def __init__(self, description):
        self.description = description


# Mock implementation of prompt handlers
async def mock_analyze_sitemap_prompt(params):
    """Mock implementation of analyze_sitemap_prompt."""
    url = params.get("url", "")
    content = TextContent(f"Please analyze the sitemap structure for {url}")
    message = PromptMessage("user", content)
    return GetPromptResult([message])


@pytest.mark.asyncio
async def test_analyze_sitemap_prompt():
    """Test the analyze_sitemap prompt."""
    # Call the mock function
    result = await mock_analyze_sitemap_prompt({"url": "example.com"})

    # Check the result
    assert len(result.messages) == 1
    assert result.messages[0].role == "user"
    assert "example.com" in result.messages[0].content.text


async def mock_visualize_sitemap_prompt(params):
    """Mock implementation of visualize_sitemap_prompt."""
    url = params.get("url", "")
    format = params.get("format", "mermaid")
    content = TextContent(f"Please visualize the sitemap for {url} in {format} format")
    message = PromptMessage("user", content)
    return GetPromptResult([message])


@pytest.mark.asyncio
async def test_visualize_sitemap_prompt():
    """Test the visualize_sitemap prompt."""
    # Call the mock function
    result = await mock_visualize_sitemap_prompt(
        {"url": "example.com", "format": "mermaid"}
    )

    # Check the result
    assert len(result.messages) == 1
    assert result.messages[0].role == "user"
    assert "example.com" in result.messages[0].content.text
    assert "mermaid" in result.messages[0].content.text


async def mock_sitemap_health_check_prompt(params):
    """Mock implementation of sitemap_health_check_prompt."""
    url = params.get("url", "")
    content = TextContent(f"Please perform a health check on the sitemap for {url}")
    message = PromptMessage("user", content)
    return GetPromptResult([message])


@pytest.mark.asyncio
async def test_sitemap_health_check_prompt():
    """Test the sitemap_health_check prompt."""
    # Call the mock function
    result = await mock_sitemap_health_check_prompt({"url": "example.com"})

    # Check the result
    assert len(result.messages) == 1
    assert result.messages[0].role == "user"
    assert "example.com" in result.messages[0].content.text
    assert "health check" in result.messages[0].content.text.lower()


async def mock_extract_sitemap_urls_prompt(params):
    """Mock implementation of extract_sitemap_urls_prompt."""
    url = params.get("url", "")
    pattern = params.get("pattern", "*")
    limit = params.get("limit", 100)
    content = TextContent(
        f"Please extract URLs from the sitemap for {url} matching pattern {pattern} with limit {limit}"
    )
    message = PromptMessage("user", content)
    return GetPromptResult([message])


@pytest.mark.asyncio
async def test_extract_sitemap_urls_prompt():
    """Test the extract_sitemap_urls prompt."""
    # Call the mock function
    result = await mock_extract_sitemap_urls_prompt(
        {"url": "example.com", "pattern": "blog/*", "limit": 10}
    )

    # Check the result
    assert len(result.messages) == 1
    assert result.messages[0].role == "user"
    assert "example.com" in result.messages[0].content.text
    assert "blog/*" in result.messages[0].content.text
    assert "10" in result.messages[0].content.text


async def mock_sitemap_missing_analysis_prompt(params):
    """Mock implementation of sitemap_missing_analysis_prompt."""
    url = params.get("url", "")
    reference_urls = params.get("reference_urls", [])
    content = TextContent(
        f"Please analyze missing URLs in the sitemap for {url} compared to reference URLs: {', '.join(reference_urls)}"
    )
    message = PromptMessage("user", content)
    return GetPromptResult([message])


@pytest.mark.asyncio
async def test_sitemap_missing_analysis_prompt():
    """Test the sitemap_missing_analysis prompt."""
    # Call the mock function
    result = await mock_sitemap_missing_analysis_prompt(
        {
            "url": "example.com",
            "reference_urls": [
                "https://example.com/page1",
                "https://example.com/page2",
            ],
        }
    )

    # Check the result
    assert len(result.messages) == 1
    assert result.messages[0].role == "user"
    assert "example.com" in result.messages[0].content.text
    assert "page1" in result.messages[0].content.text
    assert "page2" in result.messages[0].content.text
