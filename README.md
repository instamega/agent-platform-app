# Agent Platform MVP

A conversational AI agent platform built with Redis Stack that provides chat functionality with persistent memory and knowledge base integration.

## Features

- **Conversational Chat**: Interactive chat interface with OpenAI GPT-4o-mini
- **Persistent Memory**: Stores chat history with semantic search for context retrieval
- **Knowledge Base**: Ingest PDF and Markdown documents for contextual responses
- **Vector Search**: Uses OpenAI embeddings for semantic similarity matching
- **Redis Stack Backend**: Leverages Redis for both structured data and vector search capabilities

## Architecture

The system uses a Redis-based key scheme:
- `agent:user:{uid}:chat:recent` - JSON array of last N conversation turns
- `agent:user:{uid}:chat:msg:{msg_id}` - HASH for each embedded chat chunk  
- `agent:kb:doc:{doc_id}:{chunk_id}` - HASH for each embedded knowledge base chunk
- `agent:config:persona` - System prompt configuration

## Prerequisites

- Python 3.8+
- Redis Stack (with vector search capabilities)
- OpenAI API key

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
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=your_redis_password_if_needed
   KB_DATA_PATH=./kb_seed_data
   ```

4. **Start Redis Stack**
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
   This will process all PDF and Markdown files in the `kb_seed_data/` directory.

3. **Set system prompt** (optional)
   ```bash
   redis-cli SET agent:config:persona "Your custom system prompt here"
   ```

## Usage

### Command Line Interface
```bash
python app.py
```

This starts an interactive chat session where you can:
- Ask questions and receive contextual responses
- Have the agent remember previous conversations
- Get answers based on the knowledge base documents

### Programmatic Usage
```python
from app import agent

# Start a conversation
response = agent(uid="user123", user_msg="Hello, how can you help me?")
print(response)
```

## Project Structure

```
├── app.py                 # Main chat agent application
├── create-indexes.py      # Sets up Redis search indexes
├── seed_kb.py            # Knowledge base document ingestion
├── requirements.txt      # Python dependencies
├── schemas/              # Redis index schema definitions
│   ├── agent-kb-schema.yaml
│   └── history-schema.yaml
└── kb_seed_data/         # Sample knowledge base documents
    ├── *.pdf
    └── *.md
```

## Key Functions

- `agent(uid, user_msg)`: Main chat function that processes user input and returns AI response
- `store_chat(uid, role, content)`: Stores conversation turns with embeddings
- `retrieve_context(uid, query)`: Retrieves relevant context from chat history and knowledge base
- `seed_kb(file_path, model_name, key_prefix)`: Processes and stores knowledge base documents

## Configuration

### Memory Settings
- Recent chat history: Last 20 turns (configurable in `store_chat`)
- Semantic search: Top 3 similar conversations and knowledge base chunks
- Chunk size: 800 characters with 100 character overlap

### Customization
- Modify `SYSTEM_PROMPT` in Redis or directly in `app.py`
- Adjust embedding model in `seed_kb.py` (default: `text-embedding-ada-002`)
- Configure LLM model in `app.py` (default: `gpt-4o-mini`)

## Troubleshooting

- **Redis connection issues**: Verify Redis Stack is running and connection details in `.env`
- **OpenAI API errors**: Check your API key and rate limits
- **Missing indexes**: Run `python create-indexes.py` to recreate search indexes
- **Empty responses**: Ensure knowledge base is seeded with `python seed_kb.py`

## Contributing

This is an MVP designed as a foundation for building more sophisticated agent platforms. Feel free to extend and customize based on your needs.