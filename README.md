# Agent Platform MVP

A conversational AI agent platform with decoupled storage architecture that provides chat functionality with persistent memory, knowledge graph capabilities, and knowledge base integration.

## Features

- **Conversational Chat**: Interactive chat interface with OpenAI GPT-4o-mini
- **Persistent Memory**: Stores chat history with semantic search for context retrieval
- **Knowledge Graph Memory**: Track entities, relationships, and observations across conversations
- **Knowledge Base**: Ingest PDF and Markdown documents for contextual responses
- **Vector Search**: Uses OpenAI embeddings for semantic similarity matching
- **Memory Management**: Full CLI interface for managing entities and relationships
- **Decoupled Storage**: FastAPI storage abstraction service supporting multiple backends
- **Multi-Backend Support**: PostgreSQL/pgvector, Neo4j, and Redis backends
- **Web Admin Panel**: Complete web-based GUI for system management and monitoring

## Architecture

The system uses a **decoupled storage architecture** with a FastAPI storage abstraction service:

### Storage Abstraction Layer
The platform now uses a dedicated **Storage Abstraction API** (`/storage-abstraction-api/`) that provides:
- **Vector Storage**: PostgreSQL with pgvector extension for embeddings and semantic search
- **Chat Storage**: PostgreSQL for conversation history and message threading
- **Graph Storage**: Neo4j for entity relationships and knowledge graph
- **Multi-tenant Support**: Tenant isolation via HTTP headers
- **RESTful API**: Versioned `/v1` endpoints with full authentication

### Legacy Redis Schema (Backward Compatibility)
For existing integrations, the system maintains support for Redis-based storage:

**Chat & History:**
- `agent:user:{uid}:chat:recent` - JSON array of last N conversation turns
- `agent:user:{uid}:chat:msg:{msg_id}` - HASH for each embedded chat chunk  

**Knowledge Base:**
- `agent:kb:doc:{doc_id}:{chunk_id}` - HASH for each embedded knowledge base chunk

**Memory Graph:**
- `agent:memory:entity:{name}` - HASH for each entity with type and observations
- `agent:memory:relations:{from}:{to}` - SET of relation types between entities
- `agent:memory:entities_by_type:{type}` - SET of entity names by type
- `agent:memory:all_entities` - SET of all entity names

**Configuration:**
- `agent:config:persona` - System prompt configuration
- `agent:config:core_instructions` - Core behavioral instructions

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (recommended for storage services)
- OpenAI API key

### Storage Backend Options
- **PostgreSQL with pgvector** (recommended for production)
- **Neo4j** (for graph storage)  
- **Redis Stack** (legacy support, with vector search capabilities)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agent-platform-mvp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Storage Abstraction API (recommended)
   STORAGE_API_URL=http://localhost:8080
   STORAGE_API_TOKEN=changeme
   STORAGE_TENANT=default
   
   # Legacy Redis Support (optional)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=your_redis_password_if_needed
   
   KB_DATA_PATH=./kb_seed_data
   ```

4. **Start Storage Services**
   
   **Option A: Storage Abstraction API (Recommended)**
   ```bash
   # Start the decoupled storage services
   cd storage-abstraction-api
   make up
   ```
   This starts PostgreSQL, Neo4j, and the FastAPI storage service.
   
   **Option B: Redis Stack (Legacy)**
   ```bash
   # Using Docker
   docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
   
   # Or install Redis Stack locally
   # Follow instructions at: https://redis.io/docs/stack/get-started/install/
   ```

## Setup

1. **Create search indexes**
   ```bash
   python create-indexes.py
   ```

2. **Seed the knowledge base** (optional)
   ```bash
   python seed_kb.py
   ```
   This will process all PDF and Markdown files in the `kb_seed_data/` directory using enhanced chunking strategies.
   
   **Advanced Knowledge Base Processing:**
   ```bash
   # Use enhanced seeder with custom options
   python seed_kb_enhanced.py ./kb_seed_data --strategy semantic --chunk-size 1500
   
   # List available chunking strategies
   python seed_kb_enhanced.py --list-strategies
   
   # Process single file with specific strategy
   python seed_kb_enhanced.py document.pdf --strategy markdown
   
   # Clear existing knowledge base first
   python seed_kb_enhanced.py ./kb_seed_data --clear
   ```

3. **Set system prompt** (optional)
   ```bash
   redis-cli SET agent:config:persona "Your custom system prompt here"
   ```

## Usage

### Web Admin Panel
```bash
python start_admin.py
```

Launch the comprehensive web-based admin interface at http://localhost:5000

**Admin Panel Features:**
- **Dashboard**: System overview with real-time statistics and health monitoring
- **Persona Management**: Configure agent personality and core instructions via web interface
- **Memory Graph**: Visual management of entities and relationships with search capabilities
- **Conversation History**: Browse and analyze user interactions with detailed message views
- **Knowledge Base**: View and manage ingested documents and chunks
- **System Configuration**: Monitor Redis health, environment variables, and system status

**Optional Arguments:**
```bash
python start_admin.py --host 0.0.0.0 --port 8080 --debug
```

### Command Line Interface
```bash
python app.py
```

This starts an interactive chat session where you can:
- Ask questions and receive contextual responses
- Have the agent remember previous conversations
- Get answers based on the knowledge base documents
- Leverage knowledge graph memory for entity and relationship awareness

### Slack Bot Integration
```bash
python slack_bot.py
```

To enable Slack integration:
1. Create a Slack app at https://api.slack.com/apps
2. Enable Socket Mode and generate an App-Level Token
3. Add Bot Token Scopes: `chat:write`, `app_mentions:read`, `im:read`, `im:write`
4. Subscribe to Bot Events: `message.im`, `app_mention`
5. Set environment variables:
   ```
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_APP_TOKEN=xapp-your-app-token
   ```

Features:
- Responds to direct messages automatically
- Responds when mentioned in channels (@botname)
- Maintains conversation history per user
- Supports threaded conversations
- Uses same knowledge base as CLI version

### Persona Management
```bash
python persona_manager.py <command> [options]
```

Manage agent personalities and core instructions:

**Persona Commands:**
- `get` - Show current persona
- `set -t "text"` - Set persona from command line
- `load -f file.txt` - Load persona from file
- `save -f file.txt` - Save current persona to file
- `clear` - Reset to default persona
- `list` - Show available persona presets

**Core Instructions Commands:**
- `core-get` - Show current core instructions
- `core-set -t "text"` - Set core instructions from command line
- `core-load -f file.txt` - Load core instructions from file
- `core-save -f file.txt` - Save current core instructions to file
- `core-clear` - Clear core instructions
- `core-list` - Show available core instruction presets

**Examples:**
```bash
# View current persona and core instructions
python persona_manager.py get
python persona_manager.py core-get

# Load a preset persona with core instructions
python persona_manager.py core-load -f core_instructions/business.txt
python persona_manager.py load -f personas/business_advisor.txt

# Set custom instructions
python persona_manager.py core-set -t "Always provide sources for claims."
python persona_manager.py set -t "You are a helpful marketing assistant."

# List available presets
python persona_manager.py list
python persona_manager.py core-list
```

**System Prompt Structure:**
The agent combines core instructions and persona into a structured system prompt:
```
=== CORE INSTRUCTIONS ===
[Core behavioral guidelines that apply to all personas]

=== PERSONA ===
[Specific role and personality traits]
```

### Memory Graph Management
```bash
python memory_manager.py <command> [options]
```

Manage entities, relationships, and observations in the knowledge graph:

**Entity Commands:**
- `create-entity --name "Name" --type "type" --observations "obs1" "obs2"` - Create entity
- `delete-entities "name1" "name2"` - Delete entities and their relations
- `get "name1" "name2"` - Retrieve specific entities
- `add-observations --entity "name" --observations "new obs1" "new obs2"` - Add observations

**Relationship Commands:**
- `create-relation --from "entity1" --to "entity2" --type "relation_type"` - Create relation
- `delete-relation --from "entity1" --to "entity2" --type "relation_type"` - Delete relation

**Search & Management:**
- `search "query"` - Search entities and relations by content
- `stats` - Show memory graph statistics
- `export filename.json` - Export entire memory graph
- `import filename.json [--clear]` - Import memory graph
- `clear [--confirm]` - Clear all memory data

**Examples:**
```bash
# Create entities
python memory_manager.py create-entity --name "Alice" --type "person" --observations "engineer" "Python expert"
python memory_manager.py create-entity --name "TechCorp" --type "company" --observations "startup" "AI focus"

# Create relationships
python memory_manager.py create-relation --from "Alice" --to "TechCorp" --type "works_at"

# Search and explore
python memory_manager.py search "tech"
python memory_manager.py get "Alice" "TechCorp"
python memory_manager.py stats

# Backup and restore
python memory_manager.py export my_memory.json
python memory_manager.py import my_memory.json --clear
```

### Programmatic Usage
```python
from app import agent, memory_graph
import asyncio

# Start a conversation
response = agent(uid="user123", user_msg="Hello, how can you help me?")
print(response)

# Access memory graph directly
async def manage_memory():
    # Create entities
    entities = [{"name": "Alice", "entityType": "person", "observations": ["engineer"]}]
    await memory_graph.create_entities(entities)
    
    # Search memory
    results = await memory_graph.search_nodes("Alice")
    print(results)

asyncio.run(manage_memory())
```

## Project Structure

```
├── app.py                 # Main chat agent application with memory integration
├── admin_panel.py         # Web-based admin interface (Flask application)
├── start_admin.py         # Admin panel startup script with dependency checks
├── memory_graph.py        # Knowledge graph manager for entity/relationship storage
├── memory_manager.py      # CLI tool for memory graph management
├── example_memory_usage.py # Demonstration of memory-enhanced agent
├── slack_bot.py          # Slack bot integration
├── persona_manager.py    # Persona and core instruction management tool
├── slack_debug.py        # Slack connection diagnostics
├── create-indexes.py     # Sets up Redis search indexes
├── seed_kb.py            # Knowledge base seeder (backward compatible)
├── seed_kb_enhanced.py   # Enhanced knowledge base seeder with advanced chunking
├── chunking_strategies.py # Multiple chunking strategy implementations
├── document_processor.py # Enhanced document extraction with PDF improvements
├── requirements.txt      # Python dependencies
├── personas/             # Persona preset files
│   ├── helpful_assistant.txt
│   ├── technical_expert.txt
│   └── business_advisor.txt
├── core_instructions/    # Core instruction preset files
│   ├── default.txt
│   ├── business.txt
│   └── technical.txt
├── schemas/              # Redis index schema definitions
│   ├── agent-kb-schema.yaml
│   └── history-schema.yaml
├── templates/            # HTML templates for admin panel
│   ├── base.html
│   ├── dashboard.html
│   ├── personas.html
│   ├── memory.html
│   ├── conversations.html
│   ├── knowledge.html
│   └── system.html
├── static/               # Static assets for admin panel
│   ├── css/
│   │   └── admin.css     # Custom admin panel styles
│   └── js/
│       └── admin.js      # Admin panel JavaScript functionality
├── storage-abstraction-api/ # FastAPI storage abstraction service
│   ├── src/app/          # Main application code
│   │   ├── adapters/     # Storage backend implementations
│   │   │   ├── vector/   # Vector storage adapters (pgvector, redis)
│   │   │   ├── chat/     # Chat storage adapters (postgres, redis)
│   │   │   └── graph/    # Graph storage adapters (neo4j)
│   │   ├── ports/        # Domain interfaces
│   │   ├── routers/      # FastAPI endpoints
│   │   ├── schema/       # Pydantic models
│   │   └── main.py       # FastAPI application
│   ├── docker/           # Docker configuration
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── client/py/        # Python client SDK
│   │   └── storage_client.py
│   ├── test_script.py    # Comprehensive API tests
│   └── README.md         # Storage API documentation
└── kb_seed_data/         # Sample knowledge base documents
    ├── *.pdf
    └── *.md
```

## Key Functions

**Core Agent Functions:**
- `agent(uid, user_msg)`: Main chat function that processes user input and returns AI response
- `store_chat(uid, role, content)`: Stores conversation turns with embeddings
- `retrieve_context(uid, query)`: Retrieves relevant context from chat history, knowledge base, and memory graph
- `seed_kb(file_path, model_name, key_prefix)`: Processes and stores knowledge base documents

**Memory Graph Functions:**
- `memory_graph.create_entities(entities)`: Create entities with types and observations
- `memory_graph.create_relations(relations)`: Create typed relationships between entities
- `memory_graph.search_nodes(query)`: Search entities and relations by content
- `memory_graph.add_observations(observations)`: Add new observations to existing entities
- `memory_graph.read_graph()`: Retrieve entire knowledge graph
- `memory_graph.get_memory_stats()`: Get comprehensive memory statistics

## Configuration

### Memory Settings
- **Chat History**: Last 20 turns (configurable in `store_chat`)
- **Semantic Search**: Top 3 similar conversations and knowledge base chunks
- **Memory Graph Context**: Top 3 relevant entities and relationships per query
- **Chunk Size**: Default 1200 characters with 200 character overlap (enhanced from 800/100)

### Knowledge Base Chunking Strategies

The system supports multiple chunking strategies for optimal document processing:

**Available Strategies:**
- **`auto`** - Automatically selects best strategy based on file type
- **`recursive`** - Enhanced recursive character splitting with better defaults (1200 chars, 200 overlap)
- **`semantic`** - Semantic chunking respecting paragraph and sentence boundaries
- **`markdown`** - Markdown-aware chunking preserving headers and document structure
- **`sliding_window`** - Sliding window approach with configurable overlap

**Strategy Selection:**
- **PDF files**: Default to `semantic` chunking for better context preservation
- **Markdown files**: Default to `markdown` chunking to preserve structure
- **Text files**: Default to `recursive` chunking with improved parameters

**Configuration Options:**
```bash
# Environment variables for chunking
export CHUNKING_STRATEGY=semantic
export EMBEDDING_MODEL=text-embedding-ada-002

# Custom chunk sizes
python seed_kb_enhanced.py ./docs --chunk-size 1500 --chunk-overlap 300
```

### Enhanced Document Processing
- **PDF Extraction**: Supports pdfplumber, PyMuPDF, or PyPDF2 (automatic fallback)
- **Metadata Preservation**: Stores document title, author, page numbers, section headers
- **Structure Awareness**: Maintains document hierarchy and formatting context
- **Error Recovery**: Graceful fallback between extraction methods

### Customization
- **Personas & Instructions**: Modify using `persona_manager.py`
- **Memory Management**: Use `memory_manager.py` for entity and relationship management
- **Models**: Adjust embedding model in environment variables (default: `text-embedding-ada-002`)
- **LLM Configuration**: Configure model in `app.py` (default: `gpt-4o-mini`)
- **Chunking**: Customize parameters per document type
- **Memory Integration**: Control memory context retrieval in `retrieve_memory_context()`

## Troubleshooting

### Storage Abstraction API Issues
- **Storage API not responding**: Check if services are running with `docker-compose ps` in `storage-abstraction-api/docker/`
- **Database connection errors**: Verify PostgreSQL and Neo4j containers are healthy
- **Authentication errors**: Ensure `Authorization: Bearer changeme` header is included in requests
- **API tests failing**: Run `python test_script.py` in the storage-abstraction-api directory

### Legacy Redis Issues
- **Redis connection issues**: Verify Redis Stack is running and connection details in `.env`
- **Missing indexes**: Run `python create-indexes.py` to recreate search indexes

### General Issues
- **OpenAI API errors**: Check your API key and rate limits
- **Empty responses**: Ensure knowledge base is seeded with `python seed_kb.py`
- **Memory not working**: Check memory graph stats with `python memory_manager.py stats`
- **Entity creation fails**: Verify storage backend connection and check for duplicate entity names
- **Memory context not appearing**: Ensure entities/relations exist and match query terms

### Migration from Redis to Storage API
If migrating from Redis to the new storage abstraction:
1. Export data from Redis using existing tools
2. Start the storage abstraction services
3. Update application code to use the storage client SDK
4. Import data through the new API endpoints

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

This is an MVP designed as a foundation for building more sophisticated agent platforms. Feel free to extend and customize based on your needs.

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.