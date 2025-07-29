import os
import glob
from redis import Redis
from dotenv import load_dotenv
from redisvl.schema import IndexSchema
from redisvl.index import SearchIndex

load_dotenv()

client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None)
)

# Get all YAML files in the schemas folder
schema_files = glob.glob("./schemas/*.yaml")

if not schema_files:
    print("No YAML schema files found in ./schemas folder")
    exit(1)

# Create indexes for each schema file
for schema_file in schema_files:
    try:
        print(f"Processing schema file: {schema_file}")
        schema = IndexSchema.from_yaml(schema_file)
        index = SearchIndex(schema, client)
        index.create()
        print(f"Index '{schema.index.name}' created successfully from {schema_file}")
    except Exception as e:
        print(f"Error creating index from {schema_file}: {e}")

print(f"Processed {len(schema_files)} schema files")