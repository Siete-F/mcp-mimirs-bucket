"""
Python client for interacting with the ArangoDB Documentation System
"""

import os
import datetime
# import json
from typing import List, Dict, Any, Optional, Tuple #Union
from dataclasses import dataclass, field, asdict
# import numpy as np

from arango import ArangoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
DB_URL = os.getenv("ARANGO_URL", "http://localhost:8529")
DB_NAME = os.getenv("ARANGO_DB", "documentation")
DB_USER = os.getenv("ARANGO_USER", "docadmin")
DB_PASS = os.getenv("ARANGO_PASSWORD", "jansiete")

# Collection names
DOC_COLLECTION = "documents"
TOPIC_COLLECTION = "topics"
REL_COLLECTION = "relationships"

@dataclass
class DocumentMetadata:
    """Metadata for a knowledge document"""
    source: str
    creator: str
    created: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    version: int = 1

@dataclass
class Document:
    """Represents a knowledge document"""
    title: str
    content: str
    tags: List[str]
    metadata: DocumentMetadata
    key: Optional[str] = None
    summary: Optional[str] = None
    confidence: float = 0.9
    embedding: Optional[List[float]] = None
    status: str = "active"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        result = asdict(self)
        if self.key:
            result["_key"] = self.key
            del result["key"]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create a Document from a dictionary"""
        doc_data = data.copy()
        if "_key" in doc_data:
            doc_data["key"] = doc_data["_key"]
            del doc_data["_key"]
        
        # Convert metadata dict to DocumentMetadata
        metadata_dict = doc_data["metadata"]
        doc_data["metadata"] = DocumentMetadata(**metadata_dict)
        
        return cls(**doc_data)


@dataclass
class Topic:
    """Represents a knowledge topic"""
    name: str
    description: str
    key: Optional[str] = None
    parent_topic: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "created": datetime.datetime.now().isoformat(),
        "creator": "system",
        "importance": 3
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        result = asdict(self)
        if self.key:
            result["_key"] = self.key
            del result["key"]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Topic':
        """Create a Topic from a dictionary"""
        topic_data = data.copy()
        if "_key" in topic_data:
            topic_data["key"] = topic_data["_key"]
            del topic_data["_key"]
        return cls(**topic_data)


@dataclass
class Relationship:
    """Represents a relationship between documents or topics"""
    from_id: str
    to_id: str
    type: str
    strength: float = 0.5
    bidirectional: bool = False
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "created": datetime.datetime.now().isoformat(),
        "creator": "system"
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        result = asdict(self)
        result["_from"] = self.from_id
        result["_to"] = self.to_id
        del result["from_id"]
        del result["to_id"]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relationship':
        """Create a Relationship from a dictionary"""
        rel_data = data.copy()
        rel_data["from_id"] = rel_data["_from"]
        rel_data["to_id"] = rel_data["_to"]
        del rel_data["_from"]
        del rel_data["_to"]
        if "_key" in rel_data:
            del rel_data["_key"]
        return cls(**rel_data)


class DocumentationSystem:
    """Client for interacting with the ArangoDB Documentation System"""
    
    def __init__(self):
        """Initialize the documentation system client"""
        # Initialize the ArangoDB client
        self.client = ArangoClient(hosts=DB_URL)
        self.db = self.client.db(DB_NAME, username=DB_USER, password=DB_PASS)
        
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
        except:
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
        document.metadata.updated = datetime.datetime.now().isoformat()
        document.metadata.version += 1
        
        try:
            doc_dict = document.to_dict()
            self.documents.update({"_key": document.key}, doc_dict)
            return True
        except:
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
        except:
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
        except:
            return None
    
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


# Usage example
if __name__ == "__main__":
    # Create system client
    doc_system = DocumentationSystem()
    
    # Create a topic
    architecture_topic = Topic(
        name="System Architecture",
        description="Documentation about the system's architecture"
    )
    
    architecture_key = doc_system.add_topic(architecture_topic)
    print(f"Created topic with key: {architecture_key}")
    
    # Add a document
    metadata = DocumentMetadata(
        source="initial_design",
        creator="john_doe"
    )
    
    architecture_doc = Document(
        title="Database Selection",
        content="We selected ArangoDB for its multi-model capabilities...",
        tags=["architecture", "database", "design"],
        metadata=metadata,
        summary="Database technology selection rationale"
    )
    
    doc_key = doc_system.add_document(architecture_doc)
    print(f"Created document with key: {doc_key}")
    
    # Link document to topic
    rel_key = doc_system.link_document_to_topic(doc_key, architecture_key)
    print(f"Created relationship with key: {rel_key}")
    
    # Search for documents
    results = doc_system.search_documents("database")
    print(f"Found {len(results)} documents matching 'database'")
    for doc in results:
        print(f" - {doc.title}")
