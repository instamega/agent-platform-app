#!/usr/bin/env python3
"""
Persona Manager for Agent Platform
Tool for loading, saving, and managing agent personas
"""

import os
import argparse
import logging
from redis import Redis
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class PersonaManager:
    def __init__(self):
        self.client = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
        self.persona_key = "agent:config:persona"
        
        try:
            self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def get_persona(self):
        """Get the current persona"""
        try:
            persona = self.client.get(self.persona_key)
            if persona:
                logger.info("Retrieved current persona from Redis")
                return persona
            else:
                logger.info("No persona found in Redis")
                return None
        except Exception as e:
            logger.error(f"Error retrieving persona: {e}")
            return None

    def set_persona(self, persona_text):
        """Set a new persona"""
        try:
            self.client.set(self.persona_key, persona_text)
            logger.info("Persona updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting persona: {e}")
            return False

    def load_from_file(self, file_path):
        """Load persona from a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                persona_text = f.read().strip()
            
            if not persona_text:
                logger.error("File is empty")
                return False
            
            if self.set_persona(persona_text):
                logger.info(f"Persona loaded from {file_path}")
                return True
            return False
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return False

    def save_to_file(self, file_path):
        """Save current persona to a text file"""
        try:
            persona = self.get_persona()
            if not persona:
                logger.error("No persona to save")
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(persona)
            
            logger.info(f"Persona saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to file {file_path}: {e}")
            return False

    def clear_persona(self):
        """Clear the current persona (reset to default)"""
        try:
            self.client.delete(self.persona_key)
            logger.info("Persona cleared (reset to default)")
            return True
        except Exception as e:
            logger.error(f"Error clearing persona: {e}")
            return False

    def list_presets(self, presets_dir="./personas"):
        """List available persona preset files"""
        try:
            if not os.path.exists(presets_dir):
                logger.info(f"Presets directory {presets_dir} does not exist")
                return []
            
            presets = []
            for file in os.listdir(presets_dir):
                if file.endswith('.txt') or file.endswith('.md'):
                    presets.append(file)
            
            logger.info(f"Found {len(presets)} persona presets")
            return sorted(presets)
            
        except Exception as e:
            logger.error(f"Error listing presets: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description="Manage agent personas")
    parser.add_argument("command", choices=["get", "set", "load", "save", "clear", "list"], 
                       help="Command to execute")
    parser.add_argument("--text", "-t", help="Persona text (for set command)")
    parser.add_argument("--file", "-f", help="File path (for load/save commands)")
    parser.add_argument("--presets-dir", default="./personas", 
                       help="Directory containing persona presets (default: ./personas)")

    args = parser.parse_args()

    try:
        manager = PersonaManager()
        
        if args.command == "get":
            persona = manager.get_persona()
            if persona:
                print("Current Persona:")
                print("-" * 50)
                print(persona)
                print("-" * 50)
            else:
                print("No persona set (using default: 'You are ChatAgent.')")
        
        elif args.command == "set":
            if not args.text:
                print("Error: --text argument required for set command")
                return 1
            
            if manager.set_persona(args.text):
                print("Persona updated successfully!")
            else:
                print("Failed to update persona")
                return 1
        
        elif args.command == "load":
            if not args.file:
                print("Error: --file argument required for load command")
                return 1
            
            if manager.load_from_file(args.file):
                print(f"Persona loaded from {args.file}")
            else:
                print(f"Failed to load persona from {args.file}")
                return 1
        
        elif args.command == "save":
            if not args.file:
                print("Error: --file argument required for save command")
                return 1
            
            if manager.save_to_file(args.file):
                print(f"Persona saved to {args.file}")
            else:
                print(f"Failed to save persona to {args.file}")
                return 1
        
        elif args.command == "clear":
            if manager.clear_persona():
                print("Persona cleared (reset to default)")
            else:
                print("Failed to clear persona")
                return 1
        
        elif args.command == "list":
            presets = manager.list_presets(args.presets_dir)
            if presets:
                print("Available persona presets:")
                for preset in presets:
                    print(f"  - {preset}")
                print(f"\nLoad with: python persona_manager.py load -f {args.presets_dir}/FILENAME")
            else:
                print(f"No persona presets found in {args.presets_dir}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())