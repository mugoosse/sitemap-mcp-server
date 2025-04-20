from datetime import datetime
import json
from decimal import Decimal
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Union


# Custom JSON encoder to handle various types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def sanitize_json_string(value: str) -> str:
    """
    Sanitize a string value that will be included in JSON output.

    This function removes control characters and other potentially
    dangerous characters that could be used for injection attacks.

    Args:
        value: The string value to sanitize

    Returns:
        Sanitized string safe for inclusion in JSON
    """
    if value is None:
        return None

    # Remove control characters
    value = re.sub(r"[\x00-\x1F\x7F]", "", value)

    # Escape backslashes and quotes to ensure valid JSON
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')

    return value


def sanitize_json_value(value: Any) -> Any:
    """
    Recursively sanitize values in a JSON-serializable object.

    Args:
        value: The value to sanitize (can be a dict, list, or primitive type)

    Returns:
        Sanitized value safe for JSON serialization
    """
    if isinstance(value, str):
        return sanitize_json_string(value)
    elif isinstance(value, dict):
        return {k: sanitize_json_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_json_value(item) for item in value]
    return value


def safe_json_dumps(obj: Union[Dict, List], **kwargs) -> str:
    """
    Safely convert a Python object to a JSON string with sanitization.

    This function first sanitizes all string values in the object to prevent
    injection attacks, then uses the CustomJSONEncoder to handle special types.

    Args:
        obj: The object to convert to JSON
        **kwargs: Additional arguments to pass to json.dumps

    Returns:
        A sanitized JSON string
    """
    # First sanitize all string values
    sanitized_obj = sanitize_json_value(obj)

    # Then use the CustomJSONEncoder for serialization
    return json.dumps(sanitized_obj, cls=CustomJSONEncoder, **kwargs)


def normalize_and_validate_url(url: str) -> Optional[str]:
    """
    Normalize a URL by adding https:// prefix if needed, then validate it.

    This function checks if a URL starts with http:// or https://, and if not,
    prefixes it with https:// before validating with is_http_url.

    Args:
        url: The URL to normalize and validate

    Returns:
        The normalized URL if valid, None otherwise
    """
    if not url:
        return None

    # Add https:// prefix if the URL doesn't start with http:// or https://
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Validate the URL
    from usp.helpers import is_http_url

    if is_http_url(url):
        return url

    return None
