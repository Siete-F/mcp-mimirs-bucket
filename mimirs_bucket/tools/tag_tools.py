"""
Tag-related MCP tools for Mimir's Bucket.
"""

import logging
from typing import List

from mcp.server.fastmcp import FastMCP
from mimirs_bucket.db import DocumentationSystem

logger = logging.getLogger("mimirs_bucket.tools.tags")

def register_tag_tools(mcp: FastMCP, doc_system: DocumentationSystem) -> None:
    """
    Register tag-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        doc_system: The documentation system instance
    """
    @mcp.tool()
    def list_tags(include_count: bool = True) -> str:
        """
        List all tags used in the knowledge base with optional usage count
        
        Args:
            include_count: Whether to include the count of documents for each tag
        """
        try:
            # Query for all unique tags and their document counts
            aql = """
            LET tag_counts = (
                FOR doc IN documents
                    FOR tag IN doc.tags
                        COLLECT t = tag WITH COUNT INTO count
                        SORT count DESC
                        RETURN {tag: t, count: count}
            )
            RETURN tag_counts
            """
            
            results = doc_system.db.aql.execute(aql)
            tag_data = list(results)[0] if results else []
            
            if not tag_data:
                return "No tags found in the knowledge base."
            
            # Format the output
            tag_count = len(tag_data)
            output = f"# Available Tags ({tag_count})\n\n"
            
            for item in tag_data:
                tag = item["tag"]
                count = item["count"]
                
                if include_count:
                    output += f"- **{tag}** ({count} document{'' if count == 1 else 's'})\n"
                else:
                    output += f"- **{tag}**\n"
            
            # Add usage hint
            output += "\n\nYou can view documents with a specific tag using: `tag://{tag_name}`"
            
            return output
        except Exception as e:
            logger.error(f"Error listing tags: {e}")
            return f"Error listing tags: {str(e)}"

def get_documents_by_tag_impl(doc_system, tag: str) -> str:
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
            
            # Include a snippet of content
            snippet = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            output += f"{snippet}\n\n"
            output += "---\n\n"
        
        return output
    except Exception as e:
        logger.error(f"Error getting documents by tag: {e}")
        return f"Error getting documents by tag: {str(e)}"
