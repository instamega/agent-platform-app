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
import time
import uuid
from dotenv import load_dotenv
from redis import Redis
from redisvl.index import SearchIndex
from redisvl.utils.vectorize import OpenAITextVectorizer
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

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
SYSTEM_PROMPT = client.get("agent:config:persona") or "You are ChatAgent."

def key_recent(uid): return f"agent:user:{uid}:chat:recent"
def key_msg(uid, mid): return f"agent:user:{uid}:chat:msg:{mid}"

def embed(txt: str): return vectorizer.embed(txt)

# ───────────────────────  MEMORY WRITE  ────────────────────────────────
def store_chat(uid: str, role: str, content: str, keep_last: int = 20):
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

# ───────────────────────  CONTEXT RETRIEVAL  ──────────────────────────
def retrieve_context(uid: str, query: str, k: int = 3):
    # recent verbatim
    recent = client.json().get(key_recent(uid)) or []
    # semantic recall (chat)
    import struct
    vec_bytes = struct.pack('f' * len(embed(query)), *embed(query))
    from redis.commands.search.query import Query
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
    return recent + sem + kb_sem

# ───────────────────────  CHAT LOOP  ───────────────────────────────────
def agent(uid: str, user_msg: str):
    store_chat(uid, "user", user_msg)
    context = retrieve_context(uid, user_msg)
    from langchain.schema import BaseMessage
    messages: list[BaseMessage] = [SystemMessage(content=str(SYSTEM_PROMPT))]
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

# ───────────────────────  CLI DEMO  ────────────────────────────────────
if __name__ == "__main__":
    uid = "demo"
    print("User> ", end="", flush=True)
    for line in iter(input, ""):
        print("Assistant:", agent(uid, line))
        print("\nUser> ", end="", flush=True)