#!/usr/bin/env python3
"""
Admin Panel for Agent Platform
Web-based GUI for managing the agent platform components
"""

import os
import json
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from redis import Redis
from dotenv import load_dotenv
from memory_graph import MemoryGraphManager
from persona_manager import PersonaManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize Redis connection
redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)

# Initialize managers
memory_graph = MemoryGraphManager(redis_client)
persona_manager = PersonaManager()

# Helper functions
def run_async(coro):
    """Helper to run async functions in Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def get_system_stats():
    """Get system statistics and health info"""
    try:
        redis_info = redis_client.info()
        memory_stats = memory_graph.get_memory_stats()
        
        # Get persona info
        current_persona = persona_manager.get_persona()
        current_core = persona_manager.get_core_instructions()
        
        # Count knowledge base documents
        kb_keys = redis_client.keys("agent:kb:doc:*")
        if kb_keys:
            # Extract unique document IDs
            doc_ids = set()
            for key in kb_keys:
                parts = key.split(':')
                if len(parts) > 3:
                    doc_ids.add(parts[3])
            kb_count = len(doc_ids)
        else:
            kb_count = 0
        
        # Count active users (users with recent chat)
        user_keys = redis_client.keys("agent:user:*:chat:recent")
        active_users = len(user_keys)
        
        return {
            'redis_info': {
                'version': redis_info.get('redis_version', 'Unknown'),
                'memory_used': redis_info.get('used_memory_human', 'Unknown'),
                'connected_clients': redis_info.get('connected_clients', 0),
                'total_keys': redis_info.get('db0', {}).get('keys', 0) if 'db0' in redis_info else 0
            },
            'memory_stats': memory_stats,
            'persona_info': {
                'has_persona': bool(current_persona),
                'has_core_instructions': bool(current_core)
            },
            'content_stats': {
                'knowledge_base_docs': kb_count,
                'active_users': active_users
            }
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return None

def get_recent_conversations(limit=10):
    """Get recent conversation activity"""
    try:
        user_keys = redis_client.keys("agent:user:*:chat:recent")
        conversations = []
        
        for key in user_keys[:limit]:
            user_id = key.split(':')[2]
            recent_chat = redis_client.json().get(key)
            if recent_chat and len(recent_chat) > 0:
                last_msg = recent_chat[-1]
                conversations.append({
                    'user_id': user_id,
                    'last_message': last_msg.get('content', '')[:100] + '...' if len(last_msg.get('content', '')) > 100 else last_msg.get('content', ''),
                    'timestamp': datetime.fromtimestamp(int(last_msg.get('ts', 0))).strftime('%Y-%m-%d %H:%M:%S'),
                    'message_count': len(recent_chat)
                })
        
        return sorted(conversations, key=lambda x: x['timestamp'], reverse=True)
    except Exception as e:
        logger.error(f"Error getting recent conversations: {e}")
        return []

# Routes
@app.route('/')
def dashboard():
    """Main dashboard"""
    stats = get_system_stats()
    recent_convos = get_recent_conversations()
    return render_template('dashboard.html', stats=stats, conversations=recent_convos)

@app.route('/personas')
def personas():
    """Persona management page"""
    current_persona = persona_manager.get_persona()
    current_core = persona_manager.get_core_instructions()
    
    # Get available presets
    persona_files = []
    core_files = []
    
    if os.path.exists('personas'):
        persona_files = [f for f in os.listdir('personas') if f.endswith('.txt')]
    if os.path.exists('core_instructions'):
        core_files = [f for f in os.listdir('core_instructions') if f.endswith('.txt')]
    
    return render_template('personas.html', 
                         current_persona=current_persona,
                         current_core=current_core,
                         persona_files=persona_files,
                         core_files=core_files)

@app.route('/personas/update', methods=['POST'])
def update_persona():
    """Update persona or core instructions"""
    try:
        action = request.form.get('action')
        
        if action == 'set_persona':
            text = request.form.get('persona_text')
            if text:
                persona_manager.set_persona(text)
                return jsonify({'success': True, 'message': 'Persona updated successfully'})
        
        elif action == 'set_core':
            text = request.form.get('core_text')
            if text:
                persona_manager.set_core_instructions(text)
                return jsonify({'success': True, 'message': 'Core instructions updated successfully'})
        
        elif action == 'load_persona':
            filename = request.form.get('filename')
            if filename and os.path.exists(f'personas/{filename}'):
                with open(f'personas/{filename}', 'r') as f:
                    content = f.read()
                persona_manager.set_persona(content)
                return jsonify({'success': True, 'message': f'Loaded persona from {filename}'})
        
        elif action == 'load_core':
            filename = request.form.get('filename')
            if filename and os.path.exists(f'core_instructions/{filename}'):
                with open(f'core_instructions/{filename}', 'r') as f:
                    content = f.read()
                persona_manager.set_core_instructions(content)
                return jsonify({'success': True, 'message': f'Loaded core instructions from {filename}'})
        
        elif action == 'clear_persona':
            persona_manager.clear_persona()
            return jsonify({'success': True, 'message': 'Persona cleared'})
        
        elif action == 'clear_core':
            persona_manager.clear_core_instructions()
            return jsonify({'success': True, 'message': 'Core instructions cleared'})
        
        return jsonify({'success': False, 'message': 'Invalid action or missing data'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/memory')
def memory_graph_page():
    """Memory graph management page"""
    try:
        stats = memory_graph.get_memory_stats()
        return render_template('memory.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading memory page: {e}")
        return render_template('memory.html', stats=None, error=str(e))

@app.route('/memory/entities')
def get_entities():
    """Get all entities for display"""
    try:
        all_entities = memory_graph.get_all_entities()
        return jsonify({'success': True, 'entities': all_entities})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/memory/search')
def search_memory():
    """Search memory graph"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'success': False, 'message': 'No query provided'})
        
        results = run_async(memory_graph.search_nodes(query))
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/memory/entity/create', methods=['POST'])
def create_entity():
    """Create new entity"""
    try:
        data = request.get_json()
        name = data.get('name')
        entity_type = data.get('type')
        observations = data.get('observations', [])
        
        if not name or not entity_type:
            return jsonify({'success': False, 'message': 'Name and type are required'})
        
        entities = [{
            'name': name,
            'entityType': entity_type,
            'observations': observations
        }]
        
        run_async(memory_graph.create_entities(entities))
        
        return jsonify({'success': True, 'message': f'Entity "{name}" created successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/memory/relation/create', methods=['POST'])
def create_relation():
    """Create new relationship"""
    try:
        data = request.get_json()
        from_entity = data.get('from')
        to_entity = data.get('to')
        relation_type = data.get('type')
        
        if not all([from_entity, to_entity, relation_type]):
            return jsonify({'success': False, 'message': 'From, to, and type are required'})
        
        relations = [{
            'from': from_entity,
            'to': to_entity,
            'relationType': relation_type
        }]
        
        run_async(memory_graph.create_relations(relations))
        
        return jsonify({'success': True, 'message': f'Relationship created: {from_entity} --[{relation_type}]--> {to_entity}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/conversations')
def conversations():
    """Conversation history page"""
    user_keys = redis_client.keys("agent:user:*:chat:recent")
    users = []
    
    for key in user_keys:
        user_id = key.split(':')[2]
        recent_chat = redis_client.json().get(key)
        if recent_chat:
            users.append({
                'user_id': user_id,
                'message_count': len(recent_chat),
                'last_activity': datetime.fromtimestamp(int(recent_chat[-1].get('ts', 0))).strftime('%Y-%m-%d %H:%M:%S') if recent_chat else 'Unknown'
            })
    
    users.sort(key=lambda x: x['last_activity'], reverse=True)
    return render_template('conversations.html', users=users)

@app.route('/conversations/<user_id>')
def user_conversation(user_id):
    """View specific user's conversation history"""
    recent_chat = redis_client.json().get(f"agent:user:{user_id}:chat:recent") or []
    
    # Format messages for display
    messages = []
    for msg in recent_chat:
        messages.append({
            'role': msg.get('role', 'unknown'),
            'content': msg.get('content', ''),
            'timestamp': datetime.fromtimestamp(int(msg.get('ts', 0))).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return render_template('conversation_detail.html', user_id=user_id, messages=messages)

@app.route('/knowledge')
def knowledge_base():
    """Knowledge base management page"""
    # Get all knowledge base documents
    kb_keys = redis_client.keys("agent:kb:doc:*")
    documents = {}
    
    for key in kb_keys:
        parts = key.split(':')
        
        if len(parts) >= 4:
            doc_id = parts[3]
            
            if doc_id not in documents:
                documents[doc_id] = {'chunks': 1, 'sample_content': ''}
                
                # Get sample content from the document
                chunk_data = redis_client.hgetall(key)
                content = chunk_data.get('content', '')
                documents[doc_id]['sample_content'] = content[:200] + '...' if len(content) > 200 else content
            else:
                # Handle multiple chunks per document (though not expected with current format)
                documents[doc_id]['chunks'] += 1
    
    doc_list = [{'id': doc_id, 'chunks': info['chunks'], 'sample': info['sample_content']} 
                for doc_id, info in documents.items()]
    return render_template('knowledge.html', documents=doc_list)

@app.route('/system')
def system_config():
    """System configuration and health page"""
    stats = get_system_stats()
    
    # Get Redis configuration
    redis_config = {}
    try:
        config_info = redis_client.config_get('*')
        redis_config = {k: v for k, v in config_info.items() if k in ['maxmemory', 'timeout', 'databases']}
    except:
        pass
    
    # Environment variables (safe ones only)
    env_vars = {
        'REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
        'REDIS_PORT': os.getenv('REDIS_PORT', '6379'),
        'OPENAI_API_KEY': '***' if os.getenv('OPENAI_API_KEY') else 'Not Set'
    }
    
    return render_template('system.html', stats=stats, redis_config=redis_config, env_vars=env_vars)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return jsonify({'status': 'healthy', 'redis': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)