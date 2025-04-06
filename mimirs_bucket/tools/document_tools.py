"""
Document-related MCP tools for Mimir's Bucket.
"""

import logging
from typing import Optional, Any, Union
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from mimirs_bucket.db import DocumentationSystem, Document, DocumentMetadata

logger = logging.getLogger("mimirs_bucket.tools.document")

def register_document_tools(mcp: FastMCP, doc_system: DocumentationSystem) -> None:
    """
    Register document-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        doc_system: The documentation system instance
    """
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
        topic_key = str(topic_key) if topic_key else None
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
                topic = doc_system.get_topic(topic_key)
                
                if not topic:
                    return f"Document created with ID: {doc_key}, but topic '{topic_key}' not found."
                
                # Link document to topic
                doc_system.link_document_to_topic(doc_key, topic_key)
                return f"Document created with ID: {doc_key} and linked to topic '{topic.name}'."
            
            return f"Document created with ID: {doc_key}"
        except Exception as e:
            logger.error(f"Error storing knowledge: {e}")
            return f"Error storing knowledge: {str(e)}"

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
            doc1 = doc_system.get_document(str(doc1_key))
            if not doc1:
                return f"Document '{doc1_key}' not found"
            
            doc2 = doc_system.get_document(str(doc2_key))
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
