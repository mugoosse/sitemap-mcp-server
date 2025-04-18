"""
Logging configuration for the sitemap MCP server.

This module provides centralized logging configuration and a logger instance
that can be imported and used throughout the application.
"""

import os
import logging
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def configure_logger():
    """Configure and return the application logger.
    
    Returns:
        logging.Logger: The configured logger instance
    """
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create application logger
    logger = logging.getLogger("sitemap-mcp-server")
    
    # Add a file handler to keep logs in a file as well
    log_file = os.getenv("LOG_FILE", "sitemap_server.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Set log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    return logger

# Create and export the logger instance
logger = configure_logger()
