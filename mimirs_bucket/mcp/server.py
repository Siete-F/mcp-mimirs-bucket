"""
MCP server implementation for Mimir's Bucket.
"""

import logging
from textwrap import dedent
from typing import Optional

from mcp.server.fastmcp import FastMCP

from mimirs_bucket.db import DocumentationSystem
from mimirs_bucket.tools import (
    register_document_tools,
    register_search_tools,
    register_topic_tools,
    register_tag_tools
)
from mimirs_bucket.utils import load_config
from mimirs_bucket.utils.log_utils import setup_logging

logger = logging.getLogger("mimirs_bucket.mcp")

def create_server(
    config_file: Optional[str] = None, 
    db_client: Optional[DocumentationSystem] = None
) -> FastMCP:
    """
    Create and configure a Mimir's Bucket MCP server.
    
    Args:
        config_file: Optional path to config file
        db_client: Optional pre-configured database client
        
    Returns:
        Configured MCP server
    """
    # Load configuration
    config = load_config(config_file)
    
    # Setup logging
    setup_logging(level=config["mcp"]["log_level"], name="mimirs_bucket_server")
    
    # Create MCP server
    mcp = FastMCP(
        config["mcp"]["server_name"],
        dependencies=[
            "mcp",
            "python-arango",
            "python-dotenv",
            "sentence-transformers",
            "numpy"
        ]
    )
    
    # Create database client if not provided
    if not db_client:
        db_client = DocumentationSystem(
            url=config["database"]["url"],
            db_name=config["database"]["name"],
            username=config["database"]["user"],
            password=config["database"]["password"]
        )
    
    # Register tools
    register_document_tools(mcp, db_client)
    register_search_tools(mcp, db_client)
    register_topic_tools(mcp, db_client)
    register_tag_tools(mcp, db_client)
    
    # Add prompt templates
    
    @mcp.prompt()
    def store_new_knowledge(topic: str, title: str) -> str:
        """Create a new knowledge document in the system"""
        return dedent(
            f"""I want to store new information in the knowledge base.

            Topic: {topic}
            Title: {title}

            Please provide the information to store below, being as detailed and clear as possible:
            """
        )

    @mcp.prompt()
    def search_knowledge(query: str) -> str:
        """Search for information in the knowledge base"""
        return dedent(
            f"""Please search the knowledge base for information about:

            {query}

            Please provide a comprehensive answer based on all relevant knowledge you can find.
            """
        )

    return mcp

def run_server(
    mcp: FastMCP, 
    transport: str = 'stdio'
) -> None:
    """
    Run the MCP server.
    
    Args:
        mcp: The configured MCP server
        transport: Transport type ('stdio' or 'http')
    """
    # Run server with specified transport
    mcp.run(transport=transport)
