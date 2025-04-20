# Sitemap MCP Server Tests

This directory contains test cases for the Sitemap MCP Server. The tests are designed to verify the functionality of all components using a streamlined approach with minimal dependencies.

## Test Types

The testing suite is organized into the following categories:

- **Unit Tests**: Tests for individual functions and components
  - `test_pagination.py`: Tests for pagination functionality
  - `tools/test_sitemap_pages.py`: Tests for the sitemap pages tool
  - `tools/test_sitemap_stats.py`: Tests for the sitemap stats tool
  
- **Prompt Tests**: Tests for prompt handler functions
  - `prompts/test_prompts.py`: Tests for all prompt implementations

## Setting Up the Test Environment

```bash
# Install the package with test dependencies
uv pip install -e ".[test]"

# Or install test dependencies separately
uv pip install pytest pytest-asyncio
```

## Running Tests

Tests should be run using `uv run` to ensure all dependencies are properly available in the virtual environment:

```bash
# Run all tests
uv run -m pytest

# Run tests with verbose output
uv run -m pytest -v
```

### Running Specific Tests

To run specific tests, you can use the following commands:

```bash
# Run pagination tests
uv run -m pytest tests/test_pagination.py

# Run tool tests
uv run -m pytest tests/tools/

# Run prompt tests
uv run -m pytest tests/prompts/
```

This approach ensures that:
1. All dependencies are properly available within the virtual environment
2. Tests run in a consistent environment regardless of global Python setup
3. The test environment matches the development environment

## Test Coverage

The tests cover:

1. **Pagination Logic**: Testing that cursor-based pagination works correctly for sitemap pages
   - First page retrieval
   - Subsequent pages using cursors
   - Custom page size limits
   - Error handling for invalid cursors
   - Pagination metadata validation

2. **Sitemap Statistics**: Testing sitemap statistics generation
   - Basic statistics retrieval
   - Error handling
   - Empty sitemap handling

3. **Prompt Handlers**: Testing that all prompt handlers correctly format and return the expected results
   - Analyze sitemap prompt
   - Visualize sitemap prompt
   - Health check prompt
   - URL extraction prompt
   - Missing analysis prompt
   
4. **Unit Testing with Mocks**: Testing with controlled data
   - Mocking sitemap responses
   - Testing pagination logic
   - Cursor generation and validation
   - Verification of page uniqueness

## Testing Approach

The sitemap-mcp-server tests follow these principles:

1. **Unit Testing**: Each component is tested in isolation to ensure it behaves as expected.

2. **Mock Testing**: External dependencies are mocked to ensure tests are reliable and fast.

3. **Prompt Testing**: Prompt templates are tested to ensure they generate the expected output.

## Adding New Tests

When adding new functionality to the server, please ensure it is covered by tests. Follow these guidelines:

1. Use pytest fixtures for reusable test components
2. Mock external dependencies for reliable testing
3. Use `pytest.mark.asyncio` for testing async functions
4. Create isolated tests that don't depend on external services
5. Follow the existing patterns for organizing tests by functionality
