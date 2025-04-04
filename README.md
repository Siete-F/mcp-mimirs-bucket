# MCP Knowledge Base Server

This project implements a Model Context Protocol (MCP) server that connects to an ArangoDB-based knowledge management system, enabling LLMs like Claude to store, retrieve, and manage knowledge dynamically.

## Features

- **Knowledge Storage**: Store and organize information in a structured knowledge base
- **Topic Management**: Organize knowledge into hierarchical topics
- **Relationship Modeling**: Create connections between related knowledge items
- **Semantic Search**: Find relevant information using vector embeddings and natural language queries
- **Knowledge Growth**: Automatically expand the knowledge base during conversations
- **Vector Embeddings**: Utilizes sentence-transformers for semantic understanding

## Prerequisites

- Python 3.10+
- ArangoDB (installed locally or running in Docker)
- The `arango_document_api.py` Python module (ArangoDB client)
- sentence-transformers (optional but recommended for semantic search)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/siete-F/mcp-mimirs-bucket.git
   cd mcp-mimirs-bucket
   ```

2. Create a virtual environment:
   ```bash
   uv venv venv
   source venv/Scripts/activate  # On Linux: venv\bin\activate
   ```

3. Install dependencies:
  
   ```bash
   uv pip install -e .
   ```

4. Configure the database connection by creating a `.env` file:
   ```
   ARANGO_URL=http://localhost:8529
   ARANGO_DB=documentation
   ARANGO_USER=docadmin
   ARANGO_PASSWORD=your_password
   
   # MCP Server Settings
   MCP_SERVER_NAME=KnowledgeBase
   MCP_LOG_LEVEL=INFO
   ```
   
5. Set up ArangoDB:

   **Using Docker:**
   ```bash
   docker run -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb/arangodb:3.10.4
   ```
   
   Then create the database and collections:
   ```bash
   # Create database
   docker exec -it <container_name> arangosh --server.authentication false --server.database _system --javascript.execute-string="db._createDatabase('documentation');"
   
   # Create collections
   docker exec -it <container_name> arangosh --server.authentication false --server.database documentation --javascript.execute-string="db._createDocumentCollection('documents');"
   docker exec -it <container_name> arangosh --server.authentication false --server.database documentation --javascript.execute-string="db._createDocumentCollection('topics');"
   docker exec -it <container_name> arangosh --server.authentication false --server.database documentation --javascript.execute-string="db._createEdgeCollection('relationships');"
   
   # Create user
   docker exec -it <container_name> arangosh --server.authentication false --server.database _system --javascript.execute-string="require('@arangodb/users').save('docadmin', 'your_password');"
   docker exec -it <container_name> arangosh --server.authentication false --server.database _system --javascript.execute-string="require('@arangodb/users').grantDatabase('docadmin', 'documentation');"
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
If you like to use your virtual environment, update the configuration like this:
```
    "KnowledgeBase": {
      "command": "uv",
      "args": [
        "run",
        "--python",
        "F:\\projecten\\mcp-mimirs-bucket\\.venv\\Scripts\\python.exe",
        "mcp",
        "run",
        "F:\\projecten\\mcp-mimirs-bucket\\mcp_knowledge_db.py"
      ]
    },
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
- `retrieve_knowledge` - Find relevant information using keywords
- `delete_document` - Remove a document
- `semantic_search` - Find documents using semantic meaning
- `update_embeddings` - Generate or update vector embeddings

## Prompts

The server includes these prompt templates:

- `store_new_knowledge` - Template for adding new knowledge
- `search_knowledge` - Template for searching the knowledge base

## Vector Embeddings and Semantic Search

The knowledge base includes semantic search capabilities using vector embeddings, allowing you to find documents based on meaning rather than just keyword matching.

### Setting Up Vector Search

1. **Install Required Dependencies**:
   ```bash
   pip install sentence-transformers numpy
   ```

2. **Generate Embeddings**:
   After adding documents, generate embeddings using the `update_embeddings` tool or the standalone script:
   ```
   # Using the MCP tool:
   You: I need to update vector embeddings for all documents
   
   Claude: [Uses update_embeddings tool]
   Successfully updated embeddings for 15 documents.
   ```

   Or use the standalone script for batch processing:
   ```bash
   # Update all documents
   python update_embeddings.py
   
   # Update specific documents
   python update_embeddings.py -d document_key1 -d document_key2
   
   # Dry run (no updates, just logging)
   python update_embeddings.py --dry-run
   ```

3. **Using Semantic Search**:
   ```
   You: Can you find documents about authentication even if they don't mention that word specifically?
   
   Claude: [Uses semantic_search tool]
   Semantic Search Results for: 'authentication'
   
   Found 3 semantically similar documents:
   
   1. Security Implementation (Similarity: 0.89)
      Our system uses JWT tokens for verifying user identity...
   ```

### How It Works

Semantic search uses embeddings from sentence-transformers to convert documents and queries into high-dimensional vectors. Documents with similar meaning have vectors that are close together in this space, allowing for meaning-based search rather than keyword matching.

The implementation includes two approaches:

1. **Native Vector Search** (for ArangoDB ≥ 3.12 with VECTOR_SIMILARITY support)
2. **Application-Side Computation** (fallback for older versions)

## Example Interactions

### Storing Knowledge

```
You: /store backend-auth The new JWT implementation uses RS256 algorithm instead of HS256 for enhanced security.

Claude: Document created with ID: doc12345 and linked to topic 'Backend Authentication'.
```

### Retrieving Knowledge with Keywords

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

### Semantic Search

```
You: Find documentation about user identity verification without using those exact words

Claude: [Uses semantic_search tool]
Semantic Search Results for: 'user identity verification'

Found 2 semantically similar documents:

1. Authentication Mechanisms (Similarity: 0.87)
   Our system implements several methods to confirm who users are, including JWT tokens...

2. Security Framework (Similarity: 0.79)
   User validation happens through a multi-step process involving credentials and MFA...
```

## Architecture

This MCP server connects to an ArangoDB database with three collections:

- `documents` - Knowledge fragments with vector embeddings
- `topics` - Knowledge organization categories
- `relationships` - Connections between documents and topics

The architecture follows the MCP protocol to expose database functionality through resources, tools, and prompts.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │       │                 │
│  Claude or      ◄───────►  MCP Knowledge  ◄───────►  ArangoDB       │
│  other AI       │       │  Server         │       │  Database       │
│                 │       │                 │       │                 │
└─────────────────┘       └─────────────────┘       └─────────────────┘
                             │
                             │ generates
                             ▼
                          ┌─────────────────┐
                          │                 │
                          │  Vector         │
                          │  Embeddings     │
                          │                 │
                          └─────────────────┘
```

## Development

To extend this server:

1. Add new resources for additional access patterns
2. Implement more tools for specific knowledge operations
3. Create additional prompt templates for common workflows
4. Enhance semantic search with more advanced embedding models
5. Add visualization capabilities for knowledge relationships

## License

MIT License
