"""
Vector search functionality for Mimir's Bucket.

This module provides semantic search capabilities using vector embeddings.
"""

import logging
from typing import List, Tuple, Optional
import numpy as np

from mimirs_bucket.db import Document, DocumentationSystem
from mimirs_bucket.search.embeddings import (
    get_embeddings, 
    truncate_vector_for_display, 
    search_with_vector_similarity,
    search_with_app_computation,
    generate_and_store_embedding
)

logger = logging.getLogger("mimirs_bucket.vector_search")

class VectorSearch:
    """
    Vector search implementation for ArangoDB-based knowledge base.
    
    This class provides semantic search functionality by using vector embeddings
    to find documents with similar meaning regardless of exact keyword matches.
    """
    
    def __init__(self, doc_system: DocumentationSystem):
        """
        Initialize with a DocumentationSystem instance.
        
        Args:
            doc_system: The documentation system instance
        """
        self.doc_system = doc_system
        self.db = doc_system.db
    
    def search(self, query: str, limit: int = 10, min_score: float = 0.5) -> List[Tuple[Document, float]]:
        """
        Perform semantic search using vector embeddings.
        
        Args:
            query: The search query
            limit: Maximum number of results
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of (document, similarity_score) tuples
        """
        try:
            # Generate embedding for the query
            query_embedding = get_embeddings(query)
            logger.info(f"Query embedding for '{query}': {truncate_vector_for_display(query_embedding)}")
            
            # First, check if ArangoDB version supports VECTOR_SIMILARITY
            try:
                # Try to use native VECTOR_SIMILARITY if available
                return search_with_vector_similarity(self.db, query_embedding, limit, min_score)
            except Exception as e:
                logger.info(f"VECTOR_SIMILARITY not available: {e}. Using alternative approach.")
                # Fall back to application-side computation
                return search_with_app_computation(self.db, query_embedding, limit, min_score)
                
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    
    def update_document_embeddings(self, doc_key: Optional[str] = None) -> int:
        """
        Update embeddings for documents.
        
        Args:
            doc_key: Specific document key to update, or None for all documents
            
        Returns:
            Number of documents updated
        """
        count = 0
        
        if doc_key:
            # Update a specific document
            success = generate_and_store_embedding(self.doc_system, doc_key)
            if success:
                count = 1
        else:
            # Update all documents
            aql = """
            FOR doc IN documents
                RETURN doc
            """
            
            results = self.db.aql.execute(aql)
            
            for doc_dict in results:
                doc = Document.from_dict(doc_dict)
                if doc.key and generate_and_store_embedding(self.doc_system, doc.key):
                    count += 1
        
        return count
