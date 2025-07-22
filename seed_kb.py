import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from redis import Redis
import dotenv
import PyPDF2

dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KB_DATA_PATH = os.getenv("KB_DATA_PATH")
r = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)
r.ping()

def extract_text(file_path):
    if file_path.endswith('.md'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif file_path.endswith('.pdf'):
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    else:
        raise ValueError("Unsupported file type: " + file_path)

def seed_kb(file_path, model_name, key_prefix):
    text = extract_text(file_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    embeddings = OpenAIEmbeddings(model=model_name, openai_api_key=OPENAI_API_KEY)
    for chunk in splitter.split_text(text):
        r.hset(f"{key_prefix}:{hash(chunk)}", mapping={
            "content": chunk,
            "vector": json.dumps(embeddings.embed_query(chunk))
        })

file_paths = [os.path.join(KB_DATA_PATH, f) for f in os.listdir(KB_DATA_PATH) if f.endswith(".md") or f.endswith(".pdf")]
model_name = "text-embedding-ada-002"
key_prefix = "kb:embed"

for file_path in file_paths:
    seed_kb(file_path, model_name, key_prefix)

