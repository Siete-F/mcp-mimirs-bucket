"""
Search functionality for the knowledge base.

This package provides various search methods for the knowledge base,
including semantic search using vector embeddings.
"""

from .vector_search import VectorSearch
from .smart_search import SmartSearch
from .mcp_tools import register_search_tools

__all__ = ['VectorSearch', 'SmartSearch', 'register_search_tools']
