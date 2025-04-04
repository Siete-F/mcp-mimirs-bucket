"""
Data models for the ArangoDB database.
"""

import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

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
        
        # Handle ArangoDB specific fields
        if "_key" in doc_data:
            doc_data["key"] = doc_data["_key"]
            del doc_data["_key"]
        
        # Remove other ArangoDB system fields that don't map to our model
        for field in ["_id", "_rev"]:
            if field in doc_data:
                del doc_data[field]
        
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
        
        # Handle ArangoDB specific fields
        if "_key" in topic_data:
            topic_data["key"] = topic_data["_key"]
            del topic_data["_key"]
        
        # Remove other ArangoDB system fields that don't map to our model
        for field in ["_id", "_rev"]:
            if field in topic_data:
                del topic_data[field]
                
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
        
        # Convert ArangoDB edge fields to our model
        rel_data["from_id"] = rel_data["_from"]
        rel_data["to_id"] = rel_data["_to"]
        del rel_data["_from"]
        del rel_data["_to"]
        
        # Remove other ArangoDB system fields
        for field in ["_id", "_rev", "_key"]:
            if field in rel_data:
                del rel_data[field]
                
        return cls(**rel_data)
