"""
Configuration utilities for Mimir's Bucket.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

def load_config(env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        Dictionary of configuration values
    """
    # Load environment variables
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()
    
    # Database configuration
    config = {
        "database": {
            "url": os.getenv("ARANGO_URL", "http://localhost:8529"),
            "name": os.getenv("ARANGO_DB", "documentation"),
            "user": os.getenv("ARANGO_USER", "docadmin"),
            "password": os.getenv("ARANGO_PASSWORD", "myrootpassword"),
        },
        "mcp": {
            "server_name": os.getenv("MCP_SERVER_NAME", "MimirsBucket"),
            "log_level": os.getenv("MCP_LOG_LEVEL", "INFO"),
        },
        "embeddings": {
            "model": os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2"),
            "dimension": int(os.getenv("EMBEDDINGS_DIMENSION", "384")),
        }
    }
    
    return config
