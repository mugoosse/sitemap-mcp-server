"""
Base classes and utilities for MCP prompts.
"""
from dataclasses import dataclass


@dataclass
class Message:
    """Base class for all message types."""
    content: str


@dataclass
class UserMessage(Message):
    """A message from the user."""
    pass


@dataclass
class AssistantMessage(Message):
    """A message from the assistant."""
    pass


@dataclass
class SystemMessage(Message):
    """A system message."""
    pass
