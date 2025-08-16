#!/usr/bin/env python3
"""
Memory Manager CLI for Agent Platform
Provides command-line interface for managing the knowledge graph memory system.
"""

import asyncio
import json
import sys
import argparse
from typing import Dict, Any, List
from dotenv import load_dotenv
import os
from redis import Redis
from memory_graph import MemoryGraphManager

# Load environment and setup Redis connection
load_dotenv()
client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)

# Initialize memory graph manager
memory_graph = MemoryGraphManager(client)


def print_json(data: Dict[str, Any]):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))


async def cmd_create_entities(args):
    """Create new entities from command line or JSON file"""
    if args.file:
        try:
            with open(args.file, 'r') as f:
                entities = json.load(f)
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
            return
    else:
        # Create entity from command line arguments
        entities = [{
            "name": args.name,
            "entityType": args.type,
            "observations": args.observations or []
        }]
    
    try:
        new_entities = await memory_graph.create_entities(entities)
        print(f"Created {len(new_entities)} entities:")
        for entity in new_entities:
            print(f"  • {entity['name']} ({entity['entityType']})")
    except Exception as e:
        print(f"Error creating entities: {e}")


async def cmd_create_relations(args):
    """Create new relations from command line or JSON file"""
    if args.file:
        try:
            with open(args.file, 'r') as f:
                relations = json.load(f)
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
            return
    else:
        # Create relation from command line arguments
        relations = [{
            "from": args.from_entity,
            "to": args.to_entity,
            "relationType": args.relation_type
        }]
    
    try:
        new_relations = await memory_graph.create_relations(relations)
        print(f"Created {len(new_relations)} relations:")
        for relation in new_relations:
            print(f"  • {relation['from']} --[{relation['relationType']}]--> {relation['to']}")
    except Exception as e:
        print(f"Error creating relations: {e}")


async def cmd_add_observations(args):
    """Add observations to existing entities"""
    observations = [{
        "entityName": args.entity,
        "contents": args.observations
    }]
    
    try:
        results = await memory_graph.add_observations(observations)
        for result in results:
            print(f"Added {len(result['addedObservations'])} observations to {result['entityName']}")
            for obs in result['addedObservations']:
                print(f"  • {obs}")
    except Exception as e:
        print(f"Error adding observations: {e}")


async def cmd_search(args):
    """Search for entities and relations"""
    try:
        results = await memory_graph.search_nodes(args.query)
        print(f"Search results for '{args.query}':")
        print(f"Found {len(results['entities'])} entities and {len(results['relations'])} relations")
        
        if results['entities']:
            print("\nEntities:")
            for entity in results['entities']:
                print(f"  • {entity['name']} ({entity['entityType']})")
                if entity.get('observations'):
                    for obs in entity['observations'][:3]:  # Show first 3 observations
                        print(f"    - {obs}")
        
        if results['relations']:
            print("\nRelations:")
            for relation in results['relations']:
                print(f"  • {relation['from']} --[{relation['relationType']}]--> {relation['to']}")
    except Exception as e:
        print(f"Error searching: {e}")


async def cmd_get_entities(args):
    """Get specific entities by name"""
    try:
        results = await memory_graph.open_nodes(args.names)
        print(f"Retrieved {len(results['entities'])} entities:")
        
        for entity in results['entities']:
            print(f"\n{entity['name']} ({entity['entityType']}):")
            if entity.get('observations'):
                for obs in entity['observations']:
                    print(f"  • {obs}")
        
        if results['relations']:
            print(f"\nRelations between these entities:")
            for relation in results['relations']:
                print(f"  • {relation['from']} --[{relation['relationType']}]--> {relation['to']}")
    except Exception as e:
        print(f"Error retrieving entities: {e}")


async def cmd_delete_entities(args):
    """Delete entities and their relations"""
    try:
        await memory_graph.delete_entities(args.names)
        print(f"Deleted entities: {', '.join(args.names)}")
    except Exception as e:
        print(f"Error deleting entities: {e}")


async def cmd_delete_relations(args):
    """Delete specific relations"""
    relations = [{
        "from": args.from_entity,
        "to": args.to_entity,
        "relationType": args.relation_type
    }]
    
    try:
        await memory_graph.delete_relations(relations)
        print(f"Deleted relation: {args.from_entity} --[{args.relation_type}]--> {args.to_entity}")
    except Exception as e:
        print(f"Error deleting relation: {e}")


async def cmd_stats(args):
    """Show memory graph statistics"""
    try:
        stats = memory_graph.get_memory_stats()
        print("Memory Graph Statistics:")
        print(f"  Total Entities: {stats['entity_count']}")
        print(f"  Total Relations: {stats['relation_count']}")
        print(f"  Entity Types: {len(stats['entity_types'])}")
        
        if stats['entity_types']:
            print("\nEntities by Type:")
            for entity_type, count in stats['entities_by_type'].items():
                print(f"  • {entity_type}: {count}")
    except Exception as e:
        print(f"Error getting statistics: {e}")


async def cmd_export(args):
    """Export entire memory graph to JSON file"""
    try:
        graph = await memory_graph.read_graph()
        with open(args.file, 'w') as f:
            json.dump(graph, f, indent=2)
        print(f"Exported memory graph to {args.file}")
        print(f"  Entities: {len(graph['entities'])}")
        print(f"  Relations: {len(graph['relations'])}")
    except Exception as e:
        print(f"Error exporting graph: {e}")


async def cmd_import(args):
    """Import memory graph from JSON file"""
    try:
        with open(args.file, 'r') as f:
            graph = json.load(f)
        
        # Clear existing data if requested
        if args.clear:
            memory_graph.clear_all_memory_data()
            print("Cleared existing memory data")
        
        # Import entities
        if graph.get('entities'):
            new_entities = await memory_graph.create_entities(graph['entities'])
            print(f"Imported {len(new_entities)} entities")
        
        # Import relations
        if graph.get('relations'):
            new_relations = await memory_graph.create_relations(graph['relations'])
            print(f"Imported {len(new_relations)} relations")
            
    except Exception as e:
        print(f"Error importing graph: {e}")


async def cmd_clear(args):
    """Clear all memory data"""
    if args.confirm or input("Are you sure you want to clear ALL memory data? (yes/no): ").lower() == 'yes':
        memory_graph.clear_all_memory_data()
        print("Cleared all memory data")
    else:
        print("Operation cancelled")


def main():
    parser = argparse.ArgumentParser(description="Agent Memory Graph Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create entity command
    create_entity_parser = subparsers.add_parser('create-entity', help='Create a new entity')
    create_entity_parser.add_argument('--name', required=True, help='Entity name')
    create_entity_parser.add_argument('--type', required=True, help='Entity type')
    create_entity_parser.add_argument('--observations', nargs='*', help='Entity observations')
    create_entity_parser.add_argument('--file', help='JSON file containing entities to create')
    
    # Create relation command
    create_relation_parser = subparsers.add_parser('create-relation', help='Create a new relation')
    create_relation_parser.add_argument('--from', dest='from_entity', required=True, help='From entity')
    create_relation_parser.add_argument('--to', dest='to_entity', required=True, help='To entity')
    create_relation_parser.add_argument('--type', dest='relation_type', required=True, help='Relation type')
    create_relation_parser.add_argument('--file', help='JSON file containing relations to create')
    
    # Add observations command
    obs_parser = subparsers.add_parser('add-observations', help='Add observations to an entity')
    obs_parser.add_argument('--entity', required=True, help='Entity name')
    obs_parser.add_argument('--observations', nargs='+', required=True, help='Observations to add')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search entities and relations')
    search_parser.add_argument('query', help='Search query')
    
    # Get entities command
    get_parser = subparsers.add_parser('get', help='Get specific entities by name')
    get_parser.add_argument('names', nargs='+', help='Entity names to retrieve')
    
    # Delete entities command
    delete_entity_parser = subparsers.add_parser('delete-entities', help='Delete entities')
    delete_entity_parser.add_argument('names', nargs='+', help='Entity names to delete')
    
    # Delete relation command
    delete_relation_parser = subparsers.add_parser('delete-relation', help='Delete a relation')
    delete_relation_parser.add_argument('--from', dest='from_entity', required=True, help='From entity')
    delete_relation_parser.add_argument('--to', dest='to_entity', required=True, help='To entity')
    delete_relation_parser.add_argument('--type', dest='relation_type', required=True, help='Relation type')
    
    # Statistics command
    subparsers.add_parser('stats', help='Show memory graph statistics')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export memory graph to JSON file')
    export_parser.add_argument('file', help='Output file path')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import memory graph from JSON file')
    import_parser.add_argument('file', help='Input file path')
    import_parser.add_argument('--clear', action='store_true', help='Clear existing data before import')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all memory data')
    clear_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Command dispatch
    commands = {
        'create-entity': cmd_create_entities,
        'create-relation': cmd_create_relations,
        'add-observations': cmd_add_observations,
        'search': cmd_search,
        'get': cmd_get_entities,
        'delete-entities': cmd_delete_entities,
        'delete-relation': cmd_delete_relations,
        'stats': cmd_stats,
        'export': cmd_export,
        'import': cmd_import,
        'clear': cmd_clear,
    }
    
    try:
        client.ping()
        asyncio.run(commands[args.command](args))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()