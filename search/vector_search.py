"""
Vector search functionality for the knowledge base.

This module provides semantic search capabilities using vector embeddings.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional, Union
import numpy as np

from arango_document_api import Document, DocumentationSystem
from search.embeddings import get_embeddings, EmbeddingService, truncate_vector_for_display

logger = logging.getLogger("knowledge-mcp.vector_search")

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
        self.embedding_service = EmbeddingService()
    
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
                return self._search_with_vector_similarity(query_embedding, limit, min_score)
            except Exception as e:
                logger.info(f"VECTOR_SIMILARITY not available: {e}. Using alternative approach.")
                # Fall back to application-side computation
                return self._search_with_app_computation(query_embedding, limit, min_score)
                
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def _search_with_vector_similarity(self, query_embedding: List[float], limit: int, min_score: float) -> List[Tuple[Document, float]]:
        """
        Search using ArangoDB's native VECTOR_SIMILARITY function.
        
        Args:
            query_embedding: The embedding vector for the query
            limit: Maximum number of results
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of (document, similarity_score) tuples
        """
        # AQL query using VECTOR_SIMILARITY
        aql = """
        FOR doc IN documents
            FILTER doc.embedding != null
            
            // Calculate cosine similarity using built-in function
            LET similarity = VECTOR_SIMILARITY(doc.embedding, @embedding, "cosine")
            
            // Filter by minimum similarity threshold
            FILTER similarity >= @minScore
            
            // Sort by similarity (highest first)
            SORT similarity DESC
            
            // Limit results
            LIMIT @limit
            
            RETURN {
                doc: doc, 
                score: similarity
            }
        """
        
        # Execute query
        results = self.db.aql.execute(aql, bind_vars={
            "embedding": query_embedding,
            "minScore": min_score,
            "limit": limit
        })
        
        # Convert to Document objects with scores
        documents = []
        for result in results:
            doc = Document.from_dict(result["doc"])
            documents.append((doc, result["score"]))
        
        return documents
    
    def _search_with_app_computation(self, query_embedding: List[float], limit: int, min_score: float) -> List[Tuple[Document, float]]:
        """
        Fallback method that computes vector similarity in the application.
        
        Args:
            query_embedding: The embedding vector for the query
            limit: Maximum number of results
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of (document, similarity_score) tuples
        """
        # Fetch documents with embeddings
        aql = """
        FOR doc IN documents
            FILTER doc.embedding != null
            RETURN doc
        """
        
        results = self.db.aql.execute(aql)
        
        # Convert query embedding to numpy for faster computation
        query_vec = np.array(query_embedding)
        
        # Calculate similarity for each document
        scored_docs = []
        
        for doc_dict in results:
            doc = Document.from_dict(doc_dict)
            
            if not doc.embedding:
                continue
                
            # Calculate cosine similarity
            doc_vec = np.array(doc.embedding)
            similarity = self.embedding_service.cosine_similarity(query_vec, doc_vec)
            
            if similarity >= min_score:
                scored_docs.append((doc, float(similarity)))
        
        # Sort by similarity (descending) and limit
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:limit]
    
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
            document = self.doc_system.get_document(doc_key)
            if document:
                self._update_single_document_embedding(document)
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
                if self._update_single_document_embedding(doc):
                    count += 1
        
        return count
    
    def _update_single_document_embedding(self, document: Document) -> bool:
        """
        Update the embedding for a single document.
        
        Args:
            document: The document to update
            
        Returns:
            Success status
        """
        try:
            # Generate text for embedding
            text = f"{document.title} {document.summary or ''} {document.content}"
            logger.info(f"Generating embedding for document: {document.key} - '{document.title}'")
            
            # Generate embedding
            embedding = get_embeddings(text)
            logger.info(f"Generated embedding: {truncate_vector_for_display(embedding)}")
            
            # Update document in database
            self.db.collection("documents").update({
                "_key": document.key,
                "embedding": embedding
            })
            
            logger.info(f"Successfully updated embedding for document: {document.key}")
            return True
        except Exception as e:
            logger.error(f"Error updating embedding for document {document.key}: {e}")
            return False
