"""
Search-related MCP tools for Mimir's Bucket.
"""

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mimirs_bucket.db import DocumentationSystem
from mimirs_bucket.search import VectorSearch
from mimirs_bucket.search.embeddings import generate_and_store_embedding

logger = logging.getLogger("mimirs_bucket.tools.search")

def register_search_tools(mcp: FastMCP, doc_system: DocumentationSystem) -> None:
    """
    Register search-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        doc_system: The documentation system instance
    """
    # Create vector search handler
    vector_search = VectorSearch(doc_system)
    
    @mcp.tool()
    def semantic_search(
        query: str,
        max_results: int = 5,
        min_similarity: float = 0.5
    ) -> str:
        """
        Search the knowledge base using semantic meaning, not just keywords.
        
        This tool uses vector embeddings to find documents that are semantically
        similar to your query, even if they don't contain the exact keywords.
        
        Args:
            query: What you're looking for, only in the english natural language.
            max_results: Maximum number of results to return (1-20)
            min_similarity: Minimum similarity score (0-1)
        """
        try:
            # Validate parameters
            max_results = min(max(1, max_results), 20)  # Limit between 1-20
            min_similarity = min(max(0.1, min_similarity), 0.9)  # Limit between 0.1-0.9
            
            # Perform semantic search
            results = vector_search.search(
                query=query,
                limit=max_results,
                min_score=min_similarity
            )
            
            # Format results
            output = f"# Semantic Search Results for: '{query}'\n\n"
            
            if not results:
                output += "No semantically similar documents found.\n"
                return output
            
            output += f"Found {len(results)} semantically similar documents:\n\n"
            
            for idx, (doc, score) in enumerate(results, 1):
                output += f"## {idx}. {doc.title} (Similarity: {score:.2f})\n\n"
                
                # Add summary or snippet
                if doc.summary:
                    output += f"{doc.summary}\n\n"
                else:
                    # Extract a snippet from content
                    snippet = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                    output += f"{snippet}\n\n"
                
                # Add metadata
                output += f"**Tags**: {', '.join(doc.tags)}\n"
                output += f"**Document ID**: {doc.key}\n"
                output += f"**Created**: {doc.metadata.created}\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return f"Error performing semantic search: {str(e)}"

    @mcp.tool()
    def keyword_search(
        query: str,
        max_results: int = 10,
        search_in: str = "content"  # content, title, summary, tags
    ) -> str:
        """
        Search the knowledge base using keywords.
        
        This tool searches for documents containing specific keywords.
        
        Args:
            query: Keywords to search for
            max_results: Maximum number of results to return (1-20)
            search_in: Where to search (content, title, summary, tags)
        """
        try:
            # Validate parameters
            max_results = min(max(1, max_results), 20)  # Limit between 1-20
            
            # Determine search type
            if search_in.lower() == "tags":
                # Search by tag
                results = doc_system.get_documents_by_tag(query)
                search_type = "tag"
            else:
                # Default to content search
                results = doc_system.search_documents(query, limit=max_results)
                search_type = "keyword"
            
            # Limit results
            results = results[:max_results]
            
            # Format results
            output = f"# {search_type.title()} Search Results for: '{query}'\n\n"
            
            if not results:
                output += f"No documents found matching your {search_type} search.\n"
                return output
            
            output += f"Found {len(results)} matching documents:\n\n"
            
            for idx, doc in enumerate(results, 1):
                output += f"## {idx}. {doc.title}\n\n"
                
                # Add summary or snippet
                if doc.summary:
                    output += f"{doc.summary}\n\n"
                else:
                    # Extract a snippet from content
                    snippet = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                    output += f"{snippet}\n\n"
                
                # Add metadata
                output += f"**Tags**: {', '.join(doc.tags)}\n"
                output += f"**Document ID**: {doc.key}\n"
                output += f"**Created**: {doc.metadata.created}\n\n"
            
            return output
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return f"Error performing keyword search: {str(e)}"

def search_documents_impl(doc_system, query: str) -> str:
    """Search for documents matching the query"""
    try:
        # Clean up query
        query = query.strip()
        if not query:
            return "Empty search query"
        
        # Search for matching documents
        results = doc_system.search_documents(query, limit=20)
        
        # Format results
        output = f"# Search Results for: '{query}'\n\n"
        
        if not results:
            output += "No documents found matching your query.\n"
            return output
        
        output += f"Found {len(results)} matching documents:\n\n"
        
        for idx, doc in enumerate(results, 1):
            output += f"## {idx}. {doc.title}\n"
            if doc.summary:
                output += f"{doc.summary}\n\n"
            else:
                # Extract a snippet from content
                snippet = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                output += f"{snippet}\n\n"
            
            output += f"**Tags**: {', '.join(doc.tags)}\n"
            output += f"**Document ID**: {doc.key}\n"
            output += f"**Created**: {doc.metadata.created}\n\n"
        
        return output
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return f"Error searching documents: {str(e)}"
