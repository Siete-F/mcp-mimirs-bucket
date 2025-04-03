"""
MCP tools for semantic search functionality.

This module contains MCP tools for performing semantic search operations.
"""

import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP
from search.vector_search import VectorSearch
from arango_document_api import DocumentationSystem

logger = logging.getLogger("knowledge-mcp.search_tools")

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
            query: What you're looking for
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
    def update_embeddings(doc_key: Optional[str] = None) -> str:
        """
        Update vector embeddings for documents.
        
        This tool generates or updates vector embeddings used for semantic search.
        
        Args:
            doc_key: Optional specific document key to update (updates all if omitted)
        """
        try:
            if doc_key:
                # Update a specific document
                success = vector_search.update_document_embeddings(doc_key) > 0
                
                if success:
                    return f"Successfully updated embeddings for document {doc_key}."
                else:
                    return f"Failed to update embeddings for document {doc_key}."
            else:
                # Update all documents
                count = vector_search.update_document_embeddings()
                return f"Successfully updated embeddings for {count} documents."
                
        except Exception as e:
            logger.error(f"Error updating embeddings: {e}")
            return f"Error updating embeddings: {str(e)}"
