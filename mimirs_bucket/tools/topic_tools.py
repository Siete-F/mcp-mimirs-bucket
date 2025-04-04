"""
Topic-related MCP tools for Mimir's Bucket.
"""

import logging
from typing import Optional

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
        Update an existing topic in the knowledge base
        
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
                return f"Topic with key '{topic_key}' not found"
            
            # Update fields if provided
            if name:
                topic.name = name
            
            if description:
                topic.description = description
            
            if parent_topic_key is not None:  # Allow None to clear parent
                # Check if parent topic exists if not None
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
        Delete a topic from the knowledge base (only if it has no documents)
        
        Args:
            topic_key: The topic key to delete
        """
        try:
            # Get the topic to confirm it exists
            topic = doc_system.get_topic(topic_key)
            if not topic:
                return f"Topic with key '{topic_key}' not found"
            
            # Check if there are documents in this topic
            docs = doc_system.get_documents_by_topic(topic_key)
            if docs:
                return f"Cannot delete topic '{topic.name}' because it contains {len(docs)} documents"
            
            # Delete the topic
            success = doc_system.delete_topic(topic_key)
            
            if success:
                return f"Topic '{topic.name}' (ID: {topic_key}) deleted successfully"
            else:
                return f"Failed to delete topic '{topic_key}'"
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
            topics = hierarchy["topics"]
            
            if not topics:
                return "No topics found in the knowledge base"
            
            # Format as a readable tree
            output = "# Topic Hierarchy\n\n"
            
            def format_topic(topic, level=0):
                indent = "  " * level
                result = f"{indent}- **{topic['name']}** ({topic['key']}): {topic['description']}\n"
                
                for child in topic["children"]:
                    result += format_topic(child, level + 1)
                
                return result
            
            for topic in topics:
                output += format_topic(topic)
            
            return output
        except Exception as e:
            logger.error(f"Error listing topics: {e}")
            return f"Error listing topics: {str(e)}"
