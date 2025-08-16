"""
app.py  ·  MVP chat-agent backed entirely by Redis Stack
key scheme (2025-07): 
  agent:user:{uid}:chat:recent              – JSON array of last N turns
  agent:user:{uid}:chat:msg:{msg_id}        – HASH 1-per embedded chat chunk
  agent:kb:doc:{doc_id}:{chunk_id}          – HASH 1-per embedded KB chunk
  agent:config:persona                      – STRING/HASH system prompt
"""

import os
import json
import struct
import time
import uuid
from dotenv import load_dotenv
from redis import Redis
from redis.commands.search.query import Query
from redisvl.index import SearchIndex
from redisvl.utils.vectorize import OpenAITextVectorizer
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage, BaseMessage
from memory_graph import MemoryGraphManager

# ───────────────────────  ENV & CLIENT  ────────────────────────────────
load_dotenv()
client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)
client.ping()


# ───────────────────────  HELPERS  ─────────────────────────────────────
vectorizer = OpenAITextVectorizer()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
memory_graph = MemoryGraphManager(client)
def build_system_prompt():
    """Build system prompt by combining core instructions and persona"""
    core_instructions = client.get("agent:config:core_instructions")
    persona = client.get("agent:config:persona")
    
    # Build the combined prompt
    prompt_parts = []
    
    if core_instructions:
        prompt_parts.append("=== CORE INSTRUCTIONS ===")
        prompt_parts.append(core_instructions.strip())
        prompt_parts.append("")
    
    if persona:
        if core_instructions:
            prompt_parts.append("=== PERSONA ===")
        prompt_parts.append(persona.strip())
    else:
        # Default persona if none set
        if core_instructions:
            prompt_parts.append("=== PERSONA ===")
        prompt_parts.append("You are ChatAgent.")
    
    return "\n".join(prompt_parts)

# Build system prompt dynamically
def get_system_prompt():
    """Get the current system prompt (for compatibility)"""
    return build_system_prompt()

def key_recent(uid): return f"agent:user:{uid}:chat:recent"
def key_msg(uid, mid): return f"agent:user:{uid}:chat:msg:{mid}"

def embed(txt: str): return vectorizer.embed(txt)

# ───────────────────────  MEMORY WRITE  ────────────────────────────────
def store_chat(uid: str, role: str, content: str, keep_last: int = 20):
    try:
        ts = str(int(time.time()))
        m_id = str(uuid.uuid4())  # unique per chunk
        # 1) append raw JSON array
        log = client.json().get(key_recent(uid)) or []
        log.append({"role": role, "content": content, "ts": ts})
        client.json().set(key_recent(uid), "$", log[-keep_last:])
        # 2) embed & HSET
        if role == "user":             # only embed user turns (up to you)
            client.hset(
                key_msg(uid, m_id),
                mapping={
                    "content": content,
                    "user_id": uid,
                    "ts": ts,
                    "vector": json.dumps(embed(content))
                }
            )
    except Exception as e:
        print(f"Error storing chat for user {uid}: {e}")
        raise

# ───────────────────────  CONTEXT RETRIEVAL  ──────────────────────────
async def retrieve_memory_context(query: str, k: int = 3) -> List[Dict[str, str]]:
    """Retrieve relevant entities and relations from memory graph"""
    try:
        search_results = await memory_graph.search_nodes(query)
        memory_context = []
        
        # Add entity information
        for entity in search_results.get("entities", []):
            context_text = f"Entity: {entity['name']} ({entity['entityType']})"
            if entity.get("observations"):
                context_text += f" - {'; '.join(entity['observations'][:3])}"  # Limit observations
            memory_context.append({"role": "memory_graph", "content": context_text})
        
        # Add relationship information
        for relation in search_results.get("relations", []):
            context_text = f"Relationship: {relation['from']} --[{relation['relationType']}]--> {relation['to']}"
            memory_context.append({"role": "memory_graph", "content": context_text})
        
        return memory_context[:k]  # Limit results
    except Exception as e:
        print(f"Error retrieving memory context: {e}")
        return []

def retrieve_context(uid: str, query: str, k: int = 3):
    try:
        # recent verbatim
        recent = client.json().get(key_recent(uid)) or []
        # semantic recall (chat)
        vec_bytes = struct.pack('f' * len(embed(query)), *embed(query))
        res = client.ft("chat:embed").search(
            Query(f"@user_id:{{{uid}}}=>[KNN {k} @vector $vec AS score]").return_field("content"),
            query_params={"vec": vec_bytes}
        )
        sem = []
        if hasattr(res, 'docs'):
            sem = [{"role": "memory", "content": getattr(doc, 'content', '')} for doc in res.docs]
        # semantic recall (kb)
        kb_res = client.ft("kb:embed").search(
            Query(f"*=>[KNN {k} @vector $vec AS score]").return_field("content"),
            query_params={"vec": vec_bytes}
        )
        kb_sem = []
        if hasattr(kb_res, 'docs'):
            kb_sem = [{"role": "kb", "content": getattr(doc, 'content', '')} for doc in kb_res.docs]
        
        # Add memory graph context
        import asyncio
        try:
            memory_context = asyncio.run(retrieve_memory_context(query, k))
        except Exception as e:
            print(f"Warning: Could not retrieve memory context: {e}")
            memory_context = []
        
        return recent + sem + kb_sem + memory_context
    except Exception as e:
        print(f"Error retrieving context for user {uid}: {e}")
        # Return at least recent chat on error
        return client.json().get(key_recent(uid)) or []

# ───────────────────────  CHAT LOOP  ───────────────────────────────────
def agent(uid: str, user_msg: str):
    try:
        store_chat(uid, "user", user_msg)
        context = retrieve_context(uid, user_msg)
        messages: list[BaseMessage] = [SystemMessage(content=build_system_prompt())]
        for turn in context:
            if isinstance(turn, dict) and "content" in turn and "role" in turn:
                if turn["role"] == "user":
                    messages.append(HumanMessage(content=str(turn["content"])))
                elif turn["role"] == "assistant":
                    messages.append(AIMessage(content=str(turn["content"])))
                else:
                    messages.append(HumanMessage(content=f"(memory) {turn['content']}"))
        messages.append(HumanMessage(content=user_msg))
        reply = llm(messages).content
        store_chat(uid, "assistant", str(reply))
        return reply
    except Exception as e:
        error_msg = f"I'm sorry, I encountered an error: {e}"
        print(f"Error in agent for user {uid}: {e}")
        try:
            store_chat(uid, "assistant", error_msg)
        except:
            pass  # Don't fail if we can't store the error
        return error_msg

# ───────────────────────  CLI DEMO  ────────────────────────────────────
if __name__ == "__main__":
    uid = "demo"
    print("User> ", end="", flush=True)
    for line in iter(input, ""):
        print("Assistant:", agent(uid, line))
        print("\nUser> ", end="", flush=True)