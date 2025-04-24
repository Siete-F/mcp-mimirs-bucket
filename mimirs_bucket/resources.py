"""
Resource definitions for Mimir's Bucket MCP server.

This module registers all MCP resources that clients can access.
"""

import logging
from mcp.server.fastmcp import FastMCP

from mimirs_bucket.tools.topic_tools import get_all_topics_impl, get_topic_contents_impl
from mimirs_bucket.tools.document_tools import get_document_impl
from mimirs_bucket.tools.search_tools import search_documents_impl
from mimirs_bucket.tools.tag_tools import get_documents_by_tag_impl

logger = logging.getLogger("mimirs_bucket.resources")

def register_resources(mcp: FastMCP, db_client) -> None:
    """
    Register all resources with the MCP server.
    
    Args:
        mcp: The MCP server instance
        db_client: The database client
    """
    @mcp.resource("topics://list")
    def get_all_topics() -> str:
        """List all available knowledge topics"""
        return get_all_topics_impl(db_client)

    @mcp.resource("topics://{topic_key}")
    def get_topic_contents(topic_key: str) -> str:
        """Get all documents in a specific topic"""
        return get_topic_contents_impl(db_client, topic_key)

    @mcp.resource("document://{doc_key}")
    def get_document(doc_key: str) -> str:
        """Get a specific document's contents"""
        return get_document_impl(db_client, doc_key)

    @mcp.resource("search://{query}")
    def search_documents(query: str) -> str:
        """Search for documents matching the query"""
        return search_documents_impl(db_client, query)

    @mcp.resource("tag://{tag}")
    def get_documents_by_tag(tag: str) -> str:
        """Get all documents with a specific tag"""
        return get_documents_by_tag_impl(db_client, tag)
