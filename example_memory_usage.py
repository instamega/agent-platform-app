#!/usr/bin/env python3
"""
Example usage of the memory-enhanced agent platform
Demonstrates how the agent can now use knowledge graph memory capabilities.
"""

import asyncio
from app import agent, memory_graph

async def demo_memory_integration():
    """Demonstrate memory integration with the agent"""
    uid = "demo_user"
    
    print("=== Memory-Enhanced Agent Demo ===")
    
    # First, let's add some entities to memory
    print("\n1. Adding entities to memory graph...")
    entities = [
        {
            "name": "Alice Smith", 
            "entityType": "person", 
            "observations": ["Software engineer", "Works at DataCorp", "Expert in Python and machine learning"]
        },
        {
            "name": "DataCorp", 
            "entityType": "company", 
            "observations": ["Tech startup", "Founded in 2020", "Specializes in AI/ML solutions", "Located in Austin"]
        },
        {
            "name": "Project Alpha", 
            "entityType": "project", 
            "observations": ["ML recommendation system", "Started in Q1 2024", "Alice is the lead engineer"]
        }
    ]
    
    await memory_graph.create_entities(entities)
    
    # Add relationships
    print("2. Creating relationships...")
    relations = [
        {"from": "Alice Smith", "to": "DataCorp", "relationType": "works_at"},
        {"from": "Alice Smith", "to": "Project Alpha", "relationType": "leads"},
        {"from": "DataCorp", "to": "Project Alpha", "relationType": "owns"}
    ]
    
    await memory_graph.create_relations(relations)
    
    # Now test the agent with memory integration
    print("\n3. Testing agent with memory integration...")
    
    queries = [
        "Tell me about Alice Smith",
        "What projects is Alice working on?", 
        "What do you know about DataCorp?",
        "Who works at DataCorp?"
    ]
    
    for query in queries:
        print(f"\n--- User: {query} ---")
        response = agent(uid, query)
        print(f"Agent: {response}")
    
    # Show memory stats
    print("\n4. Memory Graph Statistics:")
    stats = memory_graph.get_memory_stats()
    print(f"  Entities: {stats['entity_count']}")
    print(f"  Relations: {stats['relation_count']}")
    print(f"  Entity Types: {stats['entity_types']}")

if __name__ == "__main__":
    try:
        asyncio.run(demo_memory_integration())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error during demo: {e}")