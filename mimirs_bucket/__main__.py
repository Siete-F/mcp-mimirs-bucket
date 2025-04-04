"""
Command-line entry point for Mimir's Bucket.
"""

import sys
import argparse
from typing import Optional, List

from mimirs_bucket.mcp import create_server, run_server

def main(args: Optional[List[str]] = None) -> int:
    """
    Command-line entry point.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code
    """
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
    
    parsed_args = parser.parse_args(args)
    
    try:
        # Create and run server
        mcp = create_server(parsed_args.config)
        run_server(mcp, parsed_args.transport)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
