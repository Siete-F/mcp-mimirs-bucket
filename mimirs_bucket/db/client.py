"""
Client for interacting with the ArangoDB Documentation System.
"""

import os
from typing import List, Dict, Any, Optional, Tuple

from arango import ArangoClient
from dotenv import load_dotenv

from .models import (
    Document, 
    Topic, 
    Relationship, 
    DOC_COLLECTION, 
    TOPIC_COLLECTION, 
    REL_COLLECTION
)

# Load environment variables from .env file
load_dotenv()

# Default configuration
DEFAULT_DB_URL = os.getenv("ARANGO_URL", "http://localhost:8529")
DEFAULT_DB_NAME = os.getenv("ARANGO_DB", "documentation")
DEFAULT_DB_USER = os.getenv("ARANGO_USER", "docadmin")
DEFAULT_DB_PASS = os.getenv("ARANGO_PASSWORD", "jansiete")


class DocumentationSystem:
    """Client for interacting with the ArangoDB Documentation System"""
    
    def __init__(self, 
                 url: str = DEFAULT_DB_URL, 
                 db_name: str = DEFAULT_DB_NAME,
                 username: str = DEFAULT_DB_USER,
                 password: str = DEFAULT_DB_PASS):
        """
        Initialize the documentation system client
        
        Args:
            url: ArangoDB server URL
            db_name: Database name
            username: Database username
            password: Database password
        """
        # Initialize the ArangoDB client
        self.client = ArangoClient(hosts=url)
        self.db = self.client.db(db_name, username=username, password=password)
        
        # Get collection references
        self.documents = self.db.collection(DOC_COLLECTION)
        self.topics = self.db.collection(TOPIC_COLLECTION)
        self.relationships = self.db.collection(REL_COLLECTION)
    
    def add_document(self, document: Document) -> str:
        """
        Add a new document to the system
        
        Args:
            document: The document to add
            
        Returns:
            The document key
        """
        doc_dict = document.to_dict()
        result = self.documents.insert(doc_dict)
        return result["_key"]
    
    def get_document(self, key: str) -> Optional[Document]:
        """
        Retrieve a document by key
        
        Args:
            key: The document key
            
        Returns:
            The document, or None if not found
        """
        try:
            doc = self.documents.get(key)
            if doc:
                return Document.from_dict(doc)
            return None
        except Exception:
            return None
    
    def update_document(self, document: Document) -> bool:
        """
        Update an existing document
        
        Args:
            document: The document to update (must have key set)
            
        Returns:
            True if successful, False otherwise
        """
        if not document.key:
            raise ValueError("Document key must be set for updates")
        
        # Update the metadata
        document.metadata.updated = Document.field_type_factory.now().isoformat()
        document.metadata.version += 1
        
        try:
            doc_dict = document.to_dict()
            self.documents.update({"_key": document.key}, doc_dict)
            return True
        except Exception:
            return False
    
    def delete_document(self, key: str) -> bool:
        """
        Delete a document
        
        Args:
            key: The document key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.documents.delete(key)
            # Also delete all relationships
            self._delete_document_relationships(key)
            return True
        except Exception:
            return False
    
    def _delete_document_relationships(self, doc_key: str) -> None:
        """Delete all relationships involving a document"""
        doc_id = f"{DOC_COLLECTION}/{doc_key}"
        query = """
        FOR rel IN relationships
            FILTER rel._from == @docId OR rel._to == @docId
            REMOVE rel IN relationships
        """
        self.db.aql.execute(query, bind_vars={"docId": doc_id})
    
    def add_topic(self, topic: Topic) -> str:
        """
        Add a new topic
        
        Args:
            topic: The topic to add
            
        Returns:
            The topic key
        """
        topic_dict = topic.to_dict()
        result = self.topics.insert(topic_dict)
        return result["_key"]
    
    def get_topic(self, key: str) -> Optional[Topic]:
        """
        Retrieve a topic by key
        
        Args:
            key: The topic key
            
        Returns:
            The topic, or None if not found
        """
        try:
            topic = self.topics.get(key)
            if topic:
                return Topic.from_dict(topic)
            return None
        except Exception:
            return None
            
    def update_topic(self, topic: Topic) -> bool:
        """
        Update an existing topic
        
        Args:
            topic: The topic to update (must have key set)
            
        Returns:
            True if successful, False otherwise
        """
        if not topic.key:
            raise ValueError("Topic key must be set for updates")
        
        try:
            topic_dict = topic.to_dict()
            self.topics.update({"_key": topic.key}, topic_dict)
            return True
        except Exception:
            return False
            
    def delete_topic(self, key: str) -> bool:
        """
        Delete a topic
        
        Args:
            key: The topic key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get documents in this topic
            docs = self.get_documents_by_topic(key)
            
            if docs:
                return False  # Can't delete topic with documents
                
            # Delete the topic
            self.topics.delete(key)
            
            # Delete any relationships involving this topic
            self._delete_topic_relationships(key)
            
            return True
        except Exception:
            return False
            
    def _delete_topic_relationships(self, topic_key: str) -> None:
        """Delete all relationships involving a topic"""
        topic_id = f"{TOPIC_COLLECTION}/{topic_key}"
        query = """
        FOR rel IN relationships
            FILTER rel._from == @topicId OR rel._to == @topicId
            REMOVE rel IN relationships
        """
        self.db.aql.execute(query, bind_vars={"topicId": topic_id})
    
    def add_relationship(self, relationship: Relationship) -> str:
        """
        Add a relationship between documents/topics
        
        Args:
            relationship: The relationship to add
            
        Returns:
            The relationship key
        """
        rel_dict = relationship.to_dict()
        result = self.relationships.insert(rel_dict)
        return result["_key"]
    
    def link_document_to_topic(self, doc_key: str, topic_key: str, 
                               rel_type: str = "belongs_to", strength: float = 0.9) -> str:
        """
        Create a relationship between a document and a topic
        
        Args:
            doc_key: Document key
            topic_key: Topic key
            rel_type: Relationship type
            strength: Relationship strength (0-1)
            
        Returns:
            The relationship key
        """
        from_id = f"{DOC_COLLECTION}/{doc_key}"
        to_id = f"{TOPIC_COLLECTION}/{topic_key}"
        
        rel = Relationship(
            from_id=from_id,
            to_id=to_id,
            type=rel_type,
            strength=strength
        )
        
        return self.add_relationship(rel)
    
    def link_related_documents(self, doc1_key: str, doc2_key: str, 
                               rel_type: str = "related", strength: float = 0.5,
                               bidirectional: bool = True) -> str:
        """
        Create a relationship between two documents
        
        Args:
            doc1_key: First document key
            doc2_key: Second document key
            rel_type: Relationship type
            strength: Relationship strength (0-1)
            bidirectional: Whether the relationship is bidirectional
            
        Returns:
            The relationship key
        """
        from_id = f"{DOC_COLLECTION}/{doc1_key}"
        to_id = f"{DOC_COLLECTION}/{doc2_key}"
        
        rel = Relationship(
            from_id=from_id,
            to_id=to_id,
            type=rel_type,
            strength=strength,
            bidirectional=bidirectional
        )
        
        return self.add_relationship(rel)
    
    def search_documents(self, query: str, limit: int = 10) -> List[Document]:
        """
        Search documents by content
        
        Args:
            query: The search query
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        aql = """
        FOR doc IN FULLTEXT(documents, 'content', @query)
            LIMIT @limit
            RETURN doc
        """
        
        results = self.db.aql.execute(aql, bind_vars={
            "query": query,
            "limit": limit
        })
        
        return [Document.from_dict(doc) for doc in results]
    
    def get_documents_by_tag(self, tag: str) -> List[Document]:
        """
        Get all documents with a specific tag
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of documents with the tag
        """
        aql = """
        FOR doc IN documents
            FILTER @tag IN doc.tags
            SORT doc.metadata.created DESC
            RETURN doc
        """
        
        results = self.db.aql.execute(aql, bind_vars={"tag": tag})
        return [Document.from_dict(doc) for doc in results]
    
    def get_documents_by_topic(self, topic_key: str) -> List[Document]:
        """
        Get all documents in a topic
        
        Args:
            topic_key: The topic key
            
        Returns:
            List of documents in the topic
        """
        topic_id = f"{TOPIC_COLLECTION}/{topic_key}"
        
        aql = """
        FOR rel IN relationships
            FILTER rel._to == @topicId
            FOR doc IN documents
                FILTER rel._from == doc._id
                RETURN doc
        """
        
        results = self.db.aql.execute(aql, bind_vars={"topicId": topic_id})
        return [Document.from_dict(doc) for doc in results]
    
    def get_related_documents(self, doc_key: str, rel_type: Optional[str] = None) -> List[Document]:
        """
        Get documents related to a specific document
        
        Args:
            doc_key: The document key
            rel_type: Optional relationship type filter
            
        Returns:
            List of related documents
        """
        doc_id = f"{DOC_COLLECTION}/{doc_key}"
        
        filter_str = "rel._from == @docId OR (rel._to == @docId AND rel.bidirectional == true)"
        if rel_type:
            filter_str += " AND rel.type == @relType"
        
        aql = f"""
        FOR rel IN relationships
            FILTER {filter_str}
            LET other_id = rel._from == @docId ? rel._to : rel._from
            FILTER STARTS_WITH(other_id, '{DOC_COLLECTION}/')
            FOR doc IN documents
                FILTER doc._id == other_id
                RETURN doc
        """
        
        bind_vars = {"docId": doc_id}
        if rel_type:
            bind_vars["relType"] = rel_type
        
        results = self.db.aql.execute(aql, bind_vars=bind_vars)
        return [Document.from_dict(doc) for doc in results]
    
    def list_topics(self) -> List[Topic]:
        """
        List all topics
        
        Returns:
            List of all topics
        """
        aql = """
        FOR topic IN topics
            SORT topic.name ASC
            RETURN topic
        """
        
        results = self.db.aql.execute(aql)
        return [Topic.from_dict(topic) for topic in results]
    
    def semantic_search(self, embedding: List[float], limit: int = 5) -> List[Tuple[Document, float]]:
        """
        Perform semantic search using vector similarity
        
        Args:
            embedding: The query embedding vector
            limit: Maximum number of results
            
        Returns:
            List of (document, similarity_score) tuples
        """
        aql = """
        FOR doc IN documents
            FILTER doc.embedding != null
            LET score = 1 - SQRT(SUM(
                FOR i IN 0..LENGTH(doc.embedding)-1
                RETURN POW(doc.embedding[i] - @embedding[i], 2)
            ))
            SORT score DESC
            LIMIT @limit
            RETURN {doc, score}
        """
        
        results = self.db.aql.execute(aql, bind_vars={
            "embedding": embedding,
            "limit": limit
        })
        
        return [(Document.from_dict(item["doc"]), item["score"]) for item in results]

    def get_topic_hierarchy(self) -> Dict[str, Any]:
        """
        Get the complete topic hierarchy
        
        Returns:
            Nested dictionary of topics
        """
        # First get all topics
        all_topics = self.list_topics()
        
        # Create a dictionary of topics by key
        topics_by_key = {topic.key: {
            "key": topic.key,
            "name": topic.name,
            "description": topic.description,
            "children": []
        } for topic in all_topics if topic.key}
        
        # Build the hierarchy
        roots = []
        for topic in all_topics:
            if topic.key and topic.parent_topic and topic.parent_topic in topics_by_key:
                # Add as child to parent
                topics_by_key[topic.parent_topic]["children"].append(topics_by_key[topic.key])
            elif topic.key:
                # This is a root topic
                roots.append(topics_by_key[topic.key])
        
        return {"topics": roots}
