"""
MCP Server for Dynamic Documentation Knowledge Base using ArangoDB
"""

from datetime import datetime
from typing import Optional, Union
import typing
import logging

from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

# Import the ArangoDB client
from arango_document_api import (
    DocumentationSystem,
    Document,
    DocumentMetadata,
    Topic,
    # Relationship
)

# Import search functionality
from search import register_search_tools

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("knowledge-mcp")

# Initialize FastMCP server
mcp = FastMCP(
    "KnowledgeBase",
    dependencies=[
        "mcp", 
        "python-arango", 
        "python-dotenv",
        "sentence-transformers",
        "numpy"
    ]
)

# Initialize the documentation system
doc_system = DocumentationSystem()

# Topic cache (to avoid frequent DB calls)
topic_cache = {}

# Initialize topic cache
try:
    topics = doc_system.list_topics()
    for topic in topics:
        if topic.key:
            topic_cache[topic.key] = topic
    logger.info(f"Loaded {len(topic_cache)} topics into cache")
except Exception as e:
    logger.error(f"Error loading topics: {e}")

# Resource: List all topics
@mcp.resource("topics://list")
def get_all_topics() -> str:
    """List all available knowledge topics"""
    try:
        topics = doc_system.list_topics()
        
        # Format as a readable text list
        result = "# Available Knowledge Topics\n\n"
        for topic in topics:
            result += f"- **{topic.name}** ({topic.key}): {topic.description}\n"
        
        return result
    except Exception as e:
        logger.error(f"Error listing topics: {e}")
        return f"Error listing topics: {str(e)}"

# Resource: Get topic contents
@mcp.resource("topics://{topic_key}")
def get_topic_contents(topic_key: str) -> str:
    """Get all documents in a specific topic"""
    try:
        # Verify topic exists
        topic = doc_system.get_topic(topic_key)
        if not topic:
            return f"Topic with key '{topic_key}' not found"
        
        # Get all documents in this topic
        documents = doc_system.get_documents_by_topic(topic_key)
        
        # Format as a readable document
        result = f"# {topic.name}\n\n{topic.description}\n\n"
        result += f"## Documents in this topic ({len(documents)})\n\n"
        
        for doc in documents:
            result += f"### {doc.title}\n"
            if doc.summary:
                result += f"{doc.summary}\n\n"
            result += f"**Tags**: {', '.join(doc.tags)}\n"
            result += f"**Document ID**: {doc.key}\n\n"
            
            # Include content for smaller documents
            if len(doc.content) < 1000:  # Only include content for smaller docs
                result += f"**Content**:\n{doc.content}\n\n"
            else:
                result += "*Document content too large to display. Use document:// resource to view full content.*\n\n"
            
            result += "---\n\n"
        
        return result
    except Exception as e:
        logger.error(f"Error getting topic contents: {e}")
        return f"Error getting topic contents: {str(e)}"

# Resource: Get document by key
@mcp.resource("document://{doc_key}")
def get_document(doc_key: str) -> str:
    """Get a specific document's contents"""
    try:
        document = doc_system.get_document(doc_key)
        if not document:
            return f"Document with key '{doc_key}' not found"
        
        # Format as a readable document
        result = f"# {document.title}\n\n"
        
        if document.summary:
            result += f"**Summary**: {document.summary}\n\n"
        
        # Get metadata
        result += "## Metadata\n\n"
        result += f"- **ID**: {document.key}\n"
        result += f"- **Tags**: {', '.join(document.tags)}\n"
        result += f"- **Created**: {document.metadata.created}\n"
        result += f"- **Updated**: {document.metadata.updated}\n"
        result += f"- **Version**: {document.metadata.version}\n"
        result += f"- **Source**: {document.metadata.source}\n"
        result += f"- **Creator**: {document.metadata.creator}\n"
        result += f"- **Confidence**: {document.confidence}\n\n"
        
        # Content
        result += "## Content\n\n"
        result += document.content
        
        # Related documents
        try:
            related_docs = doc_system.get_related_documents(doc_key)
            if related_docs:
                result += "\n\n## Related Documents\n\n"
                for rel_doc in related_docs:
                    result += f"- [{rel_doc.title}] (document://{rel_doc.key})\n"
        except Exception as e:
            logger.warning(f"Error getting related documents: {e}")
        
        return result
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        return f"Error getting document: {str(e)}"

# Resource: Search documents by query
@mcp.resource("search://{query}")
def search_documents(query: str) -> str:
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

# Resource: Get documents by tag
@mcp.resource("tag://{tag}")
def get_documents_by_tag(tag: str) -> str:
    """Get all documents with a specific tag"""
    try:
        tag = tag.strip().lower()
        
        # Search for documents with this tag
        documents = doc_system.get_documents_by_tag(tag)
        
        # Format results
        output = f"# Documents Tagged with '{tag}'\n\n"
        
        if not documents:
            output += f"No documents found with tag '{tag}'.\n"
            return output
        
        output += f"Found {len(documents)} documents:\n\n"
        
        for idx, doc in enumerate(documents, 1):
            output += f"## {idx}. {doc.title}\n"
            if doc.summary:
                output += f"{doc.summary}\n\n"
            
            output += f"**Tags**: {', '.join(doc.tags)}\n"
            output += f"**Document ID**: {doc.key}\n\n"
        
        return output
    except Exception as e:
        logger.error(f"Error getting documents by tag: {e}")
        return f"Error getting documents by tag: {str(e)}"

# Tool: Store new knowledge
@mcp.tool()
def store_knowledge(
    title: str,
    content: str,
    topic_key: Optional[Union[str, int]] = None,
    tags: Optional[str] = None,
    summary: Optional[str] = None,
) -> str:
    """
    Store a new piece of knowledge in the system
    
    Args:
        title: The title of the knowledge document
        content: The content of the knowledge document
        topic_key: Optional topic key to associate with this document
        tags: Optional comma-separated list of tags
        summary: Optional short summary of the content
    """
    topic_key = str(topic_key)
    try:
        # Process tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Create metadata
        metadata = DocumentMetadata(
            source="mcp_conversation",
            creator="mcp_user",
            created=datetime.now().isoformat(),
            updated=datetime.now().isoformat(),
            version=1
        )
        
        # Create the document
        document = Document(
            title=title,
            content=content,
            tags=tag_list,
            metadata=metadata,
            summary=summary,
            confidence=0.9
        )
        
        # Add to database
        doc_key = doc_system.add_document(document)
        
        # Link to topic if provided
        if topic_key:
            # Check if topic exists
            topic = None
            if topic_key in topic_cache:
                topic = topic_cache[topic_key]
            else:
                topic = doc_system.get_topic(topic_key)
                if topic and topic.key:
                    topic_cache[topic.key] = topic
            
            if not topic:
                return f"Document created with ID: {doc_key}, but topic '{topic_key}' not found."
            
            # Link document to topic
            doc_system.link_document_to_topic(doc_key, topic_key)
            return f"Document created with ID: {doc_key} and linked to topic '{topic.name}'."
        
        return f"Document created with ID: {doc_key}"
    except Exception as e:
        logger.error(f"Error storing knowledge: {e}")
        return f"Error storing knowledge: {str(e)}"

# Tool: Create a new topic
@mcp.tool()
def create_topic(
    name: str,
    description: str,
    parent_topic_key: Optional[str] = None
) -> str:
    """
    Create a new topic in the knowledge base
    
    Args:
        name: The name of the topic
        description: Description of the topic
        parent_topic_key: Optional parent topic key for hierarchy
    """
    try:
        # Check if parent topic exists if provided
        if parent_topic_key:
            parent_topic = doc_system.get_topic(parent_topic_key)
            if not parent_topic:
                return f"Parent topic '{parent_topic_key}' not found"
        
        # Create the topic
        topic = Topic(
            name=name,
            description=description,
            parent_topic=parent_topic_key
        )
        
        # Add to database
        topic_key = doc_system.add_topic(topic)
        
        # Update cache
        topic.key = topic_key
        topic_cache[topic_key] = topic
        
        return f"Topic created with ID: {topic_key}"
    except Exception as e:
        logger.error(f"Error creating topic: {e}")
        return f"Error creating topic: {str(e)}"

# Tool: Update existing document
@mcp.tool()
def update_document(
    doc_key: Union[str, int],
    title: Optional[str] = None,
    content: Optional[str] = None,
    summary: Optional[str] = None,
    add_tags: Optional[str] = None,
    remove_tags: Optional[str] = None
) -> str:
    """
    Update an existing document in the knowledge base
    
    Args:
        doc_key: The document key to update
        title: Optional new title
        content: Optional new content
        summary: Optional new summary
        add_tags: Optional comma-separated list of tags to add
        remove_tags: Optional comma-separated list of tags to remove
    """
    try:
        # Get the document
        document = doc_system.get_document(str(doc_key))
        if not document:
            return f"Document with key '{doc_key}' not found"
        
        # Update fields if provided
        if title:
            document.title = title
        
        if content:
            document.content = content
        
        if summary is not None:  # Allow empty string to clear summary
            document.summary = summary
        
        # Process tags to add
        if add_tags:
            new_tags = [tag.strip() for tag in add_tags.split(",") if tag.strip()]
            for tag in new_tags:
                if tag not in document.tags:
                    document.tags.append(tag)
        
        # Process tags to remove
        if remove_tags:
            remove_tag_list = [tag.strip() for tag in remove_tags.split(",") if tag.strip()]
            document.tags = [tag for tag in document.tags if tag not in remove_tag_list]
        
        # Update the document
        success = doc_system.update_document(document)
        
        if success:
            return f"Document '{doc_key}' updated successfully"
        else:
            return f"Failed to update document '{doc_key}'"
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        return f"Error updating document: {str(e)}"

# Tool: Link documents
@mcp.tool()
def link_documents(
    doc1_key: Union[str, int],
    doc2_key: Union[str, int],
    relationship_type: str = "related",
    bidirectional: bool = True
) -> str:
    """
    Create a relationship between two documents
    
    Args:
        doc1_key: First document key
        doc2_key: Second document key
        relationship_type: Type of relationship
        bidirectional: Whether the relationship goes both ways
    """
    try:
        # Verify documents exist
        doc1 = doc_system.get_document(doc1_key)
        if not doc1:
            return f"Document '{doc1_key}' not found"
        
        doc2 = doc_system.get_document(doc2_key)
        if not doc2:
            return f"Document '{doc2_key}' not found"
        
        # Create the relationship
        rel_key = doc_system.link_related_documents(
            str(doc1_key), 
            str(doc2_key), 
            rel_type=relationship_type,
            bidirectional=bidirectional
        )
        
        return f"Documents linked successfully: '{doc1.title}' {relationship_type} '{doc2.title}'"
    except Exception as e:
        logger.error(f"Error linking documents: {e}")
        return f"Error linking documents: {str(e)}"

# Tool: Retrieve relevant document by query
@mcp.tool()
def retrieve_knowledge(query: str, max_results: int = 3) -> str:
    """
    Retrieve relevant knowledge based on a query
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
    """
    try:
        # Search for documents
        results = doc_system.search_documents(query, limit=max_results)
        
        if not results:
            return "No relevant knowledge found. You may need to store this information."
        
        # Combine results into a comprehensive answer
        output = f"Retrieved {len(results)} relevant knowledge documents:\n\n"
        
        for idx, doc in enumerate(results, 1):
            output += f"## {idx}. {doc.title}\n"
            
            # Add tags and metadata
            output += f"**Tags**: {', '.join(doc.tags)}\n"
            output += f"**Last updated**: {doc.metadata.updated}\n"
            output += f"**Confidence**: {doc.confidence}\n\n"
            
            # Add content
            output += f"{doc.content}\n\n"
            output += "---\n\n"
        
        return output
    except Exception as e:
        logger.error(f"Error retrieving knowledge: {e}")
        return f"Error retrieving knowledge: {str(e)}"

# Tool: Delete document
@mcp.tool()
def delete_document(doc_key: str) -> str:
    """
    Delete a document from the knowledge base
    
    Args:
        doc_key: The document key to delete
    """
    try:
        # Get the document to confirm it exists
        document = doc_system.get_document(doc_key)
        if not document:
            return f"Document with key '{doc_key}' not found"
        
        # Delete the document
        success = doc_system.delete_document(doc_key)
        
        if success:
            return f"Document '{document.title}' (ID: {doc_key}) deleted successfully"
        else:
            return f"Failed to delete document '{doc_key}'"
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return f"Error deleting document: {str(e)}"

# Prompt: Store Knowledge Template
@mcp.prompt()
def store_new_knowledge(topic: str, title: str) -> str:
    """Create a new knowledge document in the system"""
    return f"""I want to store new information in the knowledge base.

Topic: {topic}
Title: {title}

Please provide the information to store below, being as detailed and clear as possible:

"""

# Prompt: Search Knowledge Template
@mcp.prompt()
def search_knowledge(query: str) -> str:
    """Search for information in the knowledge base"""
    return f"""Please search the knowledge base for information about:

{query}

Please provide a comprehensive answer based on all relevant knowledge you can find.
"""

# Register search tools
register_search_tools(mcp, doc_system)

# Run the server if executed directly
if __name__ == "__main__":
    mcp.run()
