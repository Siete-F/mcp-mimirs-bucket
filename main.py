#!/usr/bin/env python
"""
Main entry point for Mimir's Bucket MCP server.
"""
import sys
import argparse
from typing import Optional

from mimirs_bucket.mcp import create_server, run_server
from mimirs_bucket.utils import configure_third_party_loggers
from mimirs_bucket.utils.log_utils import setup_logging

# Global server instance that will be detected by MCP clients
mcp = None

def main(config_file: Optional[str] = None, transport: str = 'stdio'):
    """
    Main entry point for the MCP server.
    
    Args:
        config_file: Optional path to config file
        transport: Transport type to use ('stdio' or 'http')
    """
    # Setup logging
    logger = setup_logging(level="INFO", name="mimirs_bucket")
    
    # Configure other library loggers to use stderr
    configure_third_party_loggers(["transformers", "sentence_transformers", "torch"])
    
    try:
        # Create server
        logger.info(f"Starting Mimir's Bucket MCP server with {transport} transport")
        global mcp
        mcp = create_server(config_file)
        
        # Run server
        run_server(mcp, transport)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mimir's Bucket MCP Server")
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport type to use (default: stdio)"
    )
    
    args = parser.parse_args()
    main(args.config, args.transport)
