"""
Topic-related MCP tools for Mimir's Bucket.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP
from mimirs_bucket.db import DocumentationSystem, Topic

logger = logging.getLogger("mimirs_bucket.tools.topic")

def register_topic_tools(mcp: FastMCP, doc_system: DocumentationSystem) -> None:
    """
    Register topic-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        doc_system: The documentation system instance
    """
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
            
            return f"Topic created with ID: {topic_key}"
        except Exception as e:
            logger.error(f"Error creating topic: {e}")
            return f"Error creating topic: {str(e)}"
            
    @mcp.tool()
    def update_topic(
        topic_key: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent_topic_key: Optional[str] = None
    ) -> str:
        """
        Update an existing topic
        
        Args:
            topic_key: The topic key to update
            name: Optional new name
            description: Optional new description
            parent_topic_key: Optional new parent topic key
        """
        try:
            # Get the topic
            topic = doc_system.get_topic(topic_key)
            if not topic:
                return f"Topic '{topic_key}' not found"
            
            # Update fields if provided
            if name:
                topic.name = name
            
            if description:
                topic.description = description
            
            if parent_topic_key is not None:
                # Check if new parent exists if specified
                if parent_topic_key:
                    parent_topic = doc_system.get_topic(parent_topic_key)
                    if not parent_topic:
                        return f"Parent topic '{parent_topic_key}' not found"
                
                topic.parent_topic = parent_topic_key
            
            # Update the topic
            success = doc_system.update_topic(topic)
            
            if success:
                return f"Topic '{topic_key}' updated successfully"
            else:
                return f"Failed to update topic '{topic_key}'"
        except Exception as e:
            logger.error(f"Error updating topic: {e}")
            return f"Error updating topic: {str(e)}"
            
    @mcp.tool()
    def delete_topic(topic_key: str) -> str:
        """
        Delete a topic (only if it has no documents)
        
        Args:
            topic_key: The topic key to delete
        """
        try:
            # Try to delete the topic
            success = doc_system.delete_topic(topic_key)
            
            if success:
                return f"Topic '{topic_key}' deleted successfully"
            else:
                return f"Failed to delete topic '{topic_key}'. It may have associated documents."
        except Exception as e:
            logger.error(f"Error deleting topic: {e}")
            return f"Error deleting topic: {str(e)}"
            
    @mcp.tool()
    def list_topic_hierarchy() -> str:
        """
        List all topics in a hierarchical structure
        """
        try:
            # Get the topic hierarchy
            hierarchy = doc_system.get_topic_hierarchy()
            
            # Format as readable output
            result = "# Topic Hierarchy\n\n"
            
            if not hierarchy["topics"]:
                return "No topics found in the knowledge base."
            
            def format_topic(topic, depth=0):
                indent = "  " * depth
                output = f"{indent}- **{topic['name']}** ({topic['key']})\n"
                
                # Add children recursively
                for child in topic["children"]:
                    output += format_topic(child, depth + 1)
                    
                return output
            
            # Format all root topics
            for topic in hierarchy["topics"]:
                result += format_topic(topic)
            
            return result
        except Exception as e:
            logger.error(f"Error listing topic hierarchy: {e}")
            return f"Error listing topic hierarchy: {str(e)}"

def get_all_topics_impl(doc_system) -> str:
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

def get_topic_contents_impl(doc_system, topic_key: str) -> str:
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
                result += f"*Document content too large to display. Use document:// resource to view full content.*\n\n"
            
            result += "---\n\n"
        
        return result
    except Exception as e:
        logger.error(f"Error getting topic contents: {e}")
        return f"Error getting topic contents: {str(e)}"
