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
├── slack_bot.py          # Slack bot integration
├── persona_manager.py    # Persona and core instruction management tool
├── slack_debug.py        # Slack connection diagnostics
├── create-indexes.py      # Sets up Redis search indexes
├── seed_kb.py            # Knowledge base document ingestion
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