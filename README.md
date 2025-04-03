# MCP Knowledge Base Server

This project implements a Model Context Protocol (MCP) server that connects to an ArangoDB-based knowledge management system, enabling LLMs like Claude to store, retrieve, and manage knowledge dynamically.

## Features

- **Knowledge Storage**: Store and organize information in a structured knowledge base
- **Topic Management**: Organize knowledge into hierarchical topics
- **Relationship Modeling**: Create connections between related knowledge items
- **Semantic Search**: Find relevant information using natural language queries
- **Knowledge Growth**: Automatically expand the knowledge base during conversations

## Prerequisites

- Python 3.10+
- ArangoDB (installed locally or running in Docker)
- The `documentation_system.py` Python module (ArangoDB client)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/mcp-knowledge-server.git
   cd mcp-knowledge-server
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install mcp python-arango python-dotenv
   ```

4. Configure the database connection by creating a `.env` file:
   ```
   ARANGO_URL=http://localhost:8529
   ARANGO_DB=documentation
   ARANGO_USER=docadmin
   ARANGO_PASSWORD=your_password
   ```

## Usage

### Running the Server

Run the server directly:

```bash
python mcp_knowledge_db.py
```

Or use the MCP CLI for development:

```bash
mcp dev mcp_knowledge_db.py
```

### Installing with Claude Desktop

To integrate with Claude Desktop:

```bash
mcp install mcp_knowledge_db.py -n "Knowledge Base"
```

## Available Resources

The server exposes these resources:

- `topics://list` - List all available topics
- `topics://{topic_key}` - Show all documents in a topic
- `document://{doc_key}` - View a specific document
- `search://{query}` - Search for documents
- `tag://{tag}` - Show documents with a specific tag

## Available Tools

The server provides these tools:

- `store_knowledge` - Add a new document
- `create_topic` - Create a new topic
- `update_document` - Update an existing document
- `link_documents` - Create relationships between documents
- `retrieve_knowledge` - Find relevant information
- `delete_document` - Remove a document

## Prompts

The server includes these prompt templates:

- `store_new_knowledge` - Template for adding new knowledge
- `search_knowledge` - Template for searching the knowledge base

## Example Interactions

### Storing Knowledge

```
You: /store backend-auth The new JWT implementation uses RS256 algorithm instead of HS256 for enhanced security.

Claude: Document created with ID: doc12345 and linked to topic 'Backend Authentication'.
```

### Retrieving Knowledge

```
You: What authentication method do we use?

Claude: [Searches knowledge base]
Retrieved 1 relevant knowledge document:

## JWT Implementation
The new JWT implementation uses RS256 algorithm instead of HS256 for enhanced security.

**Tags**: authentication, jwt, security
**Last updated**: 2025-03-08T14:32:15
**Confidence**: 0.9
```

## Architecture

This MCP server connects to an ArangoDB database with three collections:

- `documents` - Knowledge fragments
- `topics` - Knowledge organization categories
- `relationships` - Connections between documents and topics

The architecture follows the MCP protocol to expose database functionality through resources, tools, and prompts.

## Development

To extend this server:

1. Add new resources for additional access patterns
2. Implement more tools for specific knowledge operations
3. Create additional prompt templates for common workflows

## License

MIT License
