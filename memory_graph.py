#!/usr/bin/env python3
"""
Memory Graph Manager for Agent Platform
Provides knowledge graph functionality using Redis for persistent entity and relationship storage.
Integrated from the memory_redis project.
"""

import redis
import json
from typing import List, Dict, Any, Optional
import os


class MemoryGraphManager:
    """
    Redis-based knowledge graph manager for the agent platform.
    Provides entity and relationship management for enhanced agent memory.
    """
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize with existing Redis client from agent platform"""
        self.redis = redis_client
        
        # Test connection
        try:
            self.redis.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Could not connect to Redis: {e}")
    
    def _entity_key(self, name: str) -> str:
        """Generate Redis key for entity"""
        return f"agent:memory:entity:{name}"
    
    def _relations_key(self, from_entity: str, to_entity: str) -> str:
        """Generate Redis key for relations between two entities"""
        return f"agent:memory:relations:{from_entity}:{to_entity}"
    
    def _entity_type_key(self, entity_type: str) -> str:
        """Generate Redis key for entity type index"""
        return f"agent:memory:entities_by_type:{entity_type}"
    
    def _serialize_observations(self, observations: List[str]) -> str:
        """Serialize observations list to JSON string"""
        return json.dumps(observations)
    
    def _deserialize_observations(self, observations_str: str) -> List[str]:
        """Deserialize observations from JSON string"""
        if not observations_str:
            return []
        return json.loads(observations_str)
    
    async def load_graph(self) -> Dict[str, Any]:
        """Load the entire knowledge graph from Redis"""
        entities = []
        relations = []
        
        # Get all entity keys
        entity_keys = self.redis.keys("agent:memory:entity:*")
        
        # Load all entities
        for key in entity_keys:
            entity_data = self.redis.hgetall(key)
            if entity_data:
                entity_name = key.split(":", 3)[3]  # Extract name from agent:memory:entity:name
                entities.append({
                    "name": entity_name,
                    "entityType": entity_data.get("entityType", ""),
                    "observations": self._deserialize_observations(entity_data.get("observations", "[]"))
                })
        
        # Get all relation keys
        relation_keys = self.redis.keys("agent:memory:relations:*")
        
        # Load all relations
        for key in relation_keys:
            parts = key.split(":", 4)  # Split agent:memory:relations:from:to
            if len(parts) >= 5:
                from_entity = parts[3]
                to_entity = parts[4]
                relation_types = self.redis.smembers(key)
                
                for relation_type in relation_types:
                    relations.append({
                        "from": from_entity,
                        "to": to_entity,
                        "relationType": relation_type
                    })
        
        return {"entities": entities, "relations": relations}
    
    async def create_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple new entities in the knowledge graph"""
        new_entities = []
        pipe = self.redis.pipeline()
        
        for entity in entities:
            entity_key = self._entity_key(entity["name"])
            
            # Check if entity already exists
            if not self.redis.exists(entity_key):
                # Add entity data
                pipe.hset(entity_key, mapping={
                    "entityType": entity["entityType"],
                    "observations": self._serialize_observations(entity["observations"])
                })
                
                # Add to type index
                pipe.sadd(self._entity_type_key(entity["entityType"]), entity["name"])
                
                # Add to all entities set
                pipe.sadd("agent:memory:all_entities", entity["name"])
                
                new_entities.append(entity)
        
        pipe.execute()
        return new_entities
    
    async def create_relations(self, relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple new relations between entities"""
        new_relations = []
        pipe = self.redis.pipeline()
        
        for relation in relations:
            from_entity = relation["from"]
            to_entity = relation["to"]
            relation_type = relation["relationType"]
            
            relations_key = self._relations_key(from_entity, to_entity)
            
            # Check if this specific relation already exists
            if not self.redis.sismember(relations_key, relation_type):
                pipe.sadd(relations_key, relation_type)
                new_relations.append(relation)
        
        pipe.execute()
        return new_relations
    
    async def add_observations(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add new observations to existing entities"""
        results = []
        
        for obs in observations:
            entity_name = obs["entityName"]
            entity_key = self._entity_key(entity_name)
            
            # Check if entity exists
            if not self.redis.exists(entity_key):
                raise ValueError(f"Entity with name {entity_name} not found")
            
            # Get current observations
            current_obs_str = self.redis.hget(entity_key, "observations") or "[]"
            current_obs = self._deserialize_observations(current_obs_str)
            
            # Filter out duplicate observations
            new_obs = [content for content in obs["contents"] if content not in current_obs]
            
            if new_obs:
                # Add new observations
                current_obs.extend(new_obs)
                self.redis.hset(entity_key, "observations", self._serialize_observations(current_obs))
            
            results.append({
                "entityName": entity_name,
                "addedObservations": new_obs
            })
        
        return results
    
    async def delete_entities(self, entity_names: List[str]) -> None:
        """Delete multiple entities and their associated relations"""
        pipe = self.redis.pipeline()
        
        for entity_name in entity_names:
            entity_key = self._entity_key(entity_name)
            
            # Get entity type before deletion
            entity_data = self.redis.hgetall(entity_key)
            if entity_data and "entityType" in entity_data:
                entity_type = entity_data["entityType"]
                # Remove from type index
                pipe.srem(self._entity_type_key(entity_type), entity_name)
            
            # Delete entity
            pipe.delete(entity_key)
            
            # Remove from all entities set
            pipe.srem("agent:memory:all_entities", entity_name)
            
            # Delete all relations involving this entity
            relation_keys = (self.redis.keys(f"agent:memory:relations:{entity_name}:*") + 
                           self.redis.keys(f"agent:memory:relations:*:{entity_name}"))
            
            for rel_key in relation_keys:
                pipe.delete(rel_key)
        
        pipe.execute()
    
    async def delete_observations(self, deletions: List[Dict[str, Any]]) -> None:
        """Delete specific observations from entities"""
        for deletion in deletions:
            entity_name = deletion["entityName"]
            entity_key = self._entity_key(entity_name)
            
            # Get current observations
            current_obs_str = self.redis.hget(entity_key, "observations") or "[]"
            current_obs = self._deserialize_observations(current_obs_str)
            
            # Filter out observations to delete
            remaining_obs = [obs for obs in current_obs if obs not in deletion["observations"]]
            
            # Update observations
            self.redis.hset(entity_key, "observations", self._serialize_observations(remaining_obs))
    
    async def delete_relations(self, relations: List[Dict[str, Any]]) -> None:
        """Delete multiple relations from the knowledge graph"""
        pipe = self.redis.pipeline()
        
        for relation in relations:
            from_entity = relation["from"]
            to_entity = relation["to"]
            relation_type = relation["relationType"]
            
            relations_key = self._relations_key(from_entity, to_entity)
            pipe.srem(relations_key, relation_type)
            
            # If no more relations exist between these entities, delete the key
            if self.redis.scard(relations_key) == 1:  # Will be 0 after this removal
                pipe.delete(relations_key)
        
        pipe.execute()
    
    async def read_graph(self) -> Dict[str, Any]:
        """Read the entire knowledge graph"""
        return await self.load_graph()
    
    def clear_all_memory_data(self) -> None:
        """Clear all knowledge graph data from Redis (use with caution!)"""
        keys_to_delete = (
            self.redis.keys("agent:memory:entity:*") +
            self.redis.keys("agent:memory:relations:*") +
            self.redis.keys("agent:memory:entities_by_type:*") +
            ["agent:memory:all_entities"]
        )
        
        # Filter out empty keys
        keys_to_delete = [k for k in keys_to_delete if k]
        
        if keys_to_delete:
            self.redis.delete(*keys_to_delete)
    
    async def search_nodes(self, query: str) -> Dict[str, Any]:
        """Search for nodes in the knowledge graph based on a query"""
        query_lower = query.lower()
        filtered_entities = []
        
        # Get all entity keys
        entity_keys = self.redis.keys("agent:memory:entity:*")
        
        # Search through entities
        for key in entity_keys:
            entity_data = self.redis.hgetall(key)
            if entity_data:
                entity_name = key.split(":", 3)[3]  # Extract name from agent:memory:entity:name
                entity_type = entity_data.get("entityType", "")
                observations = self._deserialize_observations(entity_data.get("observations", "[]"))
                
                # Check if query matches name, type, or any observation
                if (query_lower in entity_name.lower() or 
                    query_lower in entity_type.lower() or
                    any(query_lower in obs.lower() for obs in observations)):
                    
                    filtered_entities.append({
                        "name": entity_name,
                        "entityType": entity_type,
                        "observations": observations
                    })
        
        # Get entity names for relation filtering
        filtered_entity_names = {entity["name"] for entity in filtered_entities}
        
        # Filter relations to only include those between filtered entities
        filtered_relations = []
        relation_keys = self.redis.keys("agent:memory:relations:*")
        
        for key in relation_keys:
            parts = key.split(":", 4)  # Split agent:memory:relations:from:to
            if len(parts) >= 5:
                from_entity = parts[3]
                to_entity = parts[4]
                
                if from_entity in filtered_entity_names and to_entity in filtered_entity_names:
                    relation_types = self.redis.smembers(key)
                    
                    for relation_type in relation_types:
                        filtered_relations.append({
                            "from": from_entity,
                            "to": to_entity,
                            "relationType": relation_type
                        })
        
        return {
            "entities": filtered_entities,
            "relations": filtered_relations
        }
    
    async def open_nodes(self, names: List[str]) -> Dict[str, Any]:
        """Open specific nodes in the knowledge graph by their names"""
        filtered_entities = []
        
        # Get entities by name
        for name in names:
            entity_key = self._entity_key(name)
            entity_data = self.redis.hgetall(entity_key)
            
            if entity_data:
                filtered_entities.append({
                    "name": name,
                    "entityType": entity_data.get("entityType", ""),
                    "observations": self._deserialize_observations(entity_data.get("observations", "[]"))
                })
        
        # Get entity names for relation filtering
        filtered_entity_names = set(names)
        
        # Filter relations to only include those between filtered entities
        filtered_relations = []
        relation_keys = self.redis.keys("agent:memory:relations:*")
        
        for key in relation_keys:
            parts = key.split(":", 4)  # Split agent:memory:relations:from:to
            if len(parts) >= 5:
                from_entity = parts[3]
                to_entity = parts[4]
                
                if from_entity in filtered_entity_names and to_entity in filtered_entity_names:
                    relation_types = self.redis.smembers(key)
                    
                    for relation_type in relation_types:
                        filtered_relations.append({
                            "from": from_entity,
                            "to": to_entity,
                            "relationType": relation_type
                        })
        
        return {
            "entities": filtered_entities,
            "relations": filtered_relations
        }
    
    def get_entity_by_type(self, entity_type: str) -> List[str]:
        """Get all entity names of a specific type"""
        return list(self.redis.smembers(self._entity_type_key(entity_type)))
    
    def get_all_entity_types(self) -> List[str]:
        """Get all entity types in the knowledge graph"""
        type_keys = self.redis.keys("agent:memory:entities_by_type:*")
        return [key.split(":", 4)[4] for key in type_keys if len(key.split(":", 4)) >= 5]
    
    def get_entity_count(self) -> int:
        """Get total number of entities"""
        return self.redis.scard("agent:memory:all_entities")
    
    def get_relation_count(self) -> int:
        """Get total number of relations"""
        relation_keys = self.redis.keys("agent:memory:relations:*")
        total_relations = 0
        for key in relation_keys:
            total_relations += self.redis.scard(key)
        return total_relations
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        return {
            "entity_count": self.get_entity_count(),
            "relation_count": self.get_relation_count(),
            "entity_types": self.get_all_entity_types(),
            "entities_by_type": {
                entity_type: len(self.get_entity_by_type(entity_type))
                for entity_type in self.get_all_entity_types()
            }
        }