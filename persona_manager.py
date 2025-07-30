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
        self.core_instructions_key = "agent:config:core_instructions"
        
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

    def get_core_instructions(self):
        """Get the current core instructions"""
        try:
            core_instructions = self.client.get(self.core_instructions_key)
            if core_instructions:
                logger.info("Retrieved current core instructions from Redis")
                return core_instructions
            else:
                logger.info("No core instructions found in Redis")
                return None
        except Exception as e:
            logger.error(f"Error retrieving core instructions: {e}")
            return None

    def set_core_instructions(self, instructions_text):
        """Set new core instructions"""
        try:
            self.client.set(self.core_instructions_key, instructions_text)
            logger.info("Core instructions updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting core instructions: {e}")
            return False

    def load_core_from_file(self, file_path):
        """Load core instructions from a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                instructions_text = f.read().strip()
            
            if not instructions_text:
                logger.error("File is empty")
                return False
            
            if self.set_core_instructions(instructions_text):
                logger.info(f"Core instructions loaded from {file_path}")
                return True
            return False
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return False

    def save_core_to_file(self, file_path):
        """Save current core instructions to a text file"""
        try:
            core_instructions = self.get_core_instructions()
            if not core_instructions:
                logger.error("No core instructions to save")
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(core_instructions)
            
            logger.info(f"Core instructions saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to file {file_path}: {e}")
            return False

    def clear_core_instructions(self):
        """Clear the current core instructions"""
        try:
            self.client.delete(self.core_instructions_key)
            logger.info("Core instructions cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing core instructions: {e}")
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

    def list_core_presets(self, presets_dir="./core_instructions"):
        """List available core instruction preset files"""
        try:
            if not os.path.exists(presets_dir):
                logger.info(f"Core instructions directory {presets_dir} does not exist")
                return []
            
            presets = []
            for file in os.listdir(presets_dir):
                if file.endswith('.txt') or file.endswith('.md'):
                    presets.append(file)
            
            logger.info(f"Found {len(presets)} core instruction presets")
            return sorted(presets)
            
        except Exception as e:
            logger.error(f"Error listing core instruction presets: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description="Manage agent personas and core instructions")
    parser.add_argument("command", choices=["get", "set", "load", "save", "clear", "list", 
                                          "core-get", "core-set", "core-load", "core-save", 
                                          "core-clear", "core-list"], 
                       help="Command to execute")
    parser.add_argument("--text", "-t", help="Text content (for set/core-set commands)")
    parser.add_argument("--file", "-f", help="File path (for load/save commands)")
    parser.add_argument("--presets-dir", default="./personas", 
                       help="Directory containing persona presets (default: ./personas)")
    parser.add_argument("--core-presets-dir", default="./core_instructions", 
                       help="Directory containing core instruction presets (default: ./core_instructions)")

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
        
        # Core instruction commands
        elif args.command == "core-get":
            core_instructions = manager.get_core_instructions()
            if core_instructions:
                print("Current Core Instructions:")
                print("-" * 50)
                print(core_instructions)
                print("-" * 50)
            else:
                print("No core instructions set")

        elif args.command == "core-set":
            if not args.text:
                print("Error: --text argument required for core-set command")
                return 1
            
            if manager.set_core_instructions(args.text):
                print("Core instructions updated successfully!")
            else:
                print("Failed to update core instructions")
                return 1

        elif args.command == "core-load":
            if not args.file:
                print("Error: --file argument required for core-load command")
                return 1
            
            if manager.load_core_from_file(args.file):
                print(f"Core instructions loaded from {args.file}")
            else:
                print(f"Failed to load core instructions from {args.file}")
                return 1

        elif args.command == "core-save":
            if not args.file:
                print("Error: --file argument required for core-save command")
                return 1
            
            if manager.save_core_to_file(args.file):
                print(f"Core instructions saved to {args.file}")
            else:
                print(f"Failed to save core instructions to {args.file}")
                return 1

        elif args.command == "core-clear":
            if manager.clear_core_instructions():
                print("Core instructions cleared")
            else:
                print("Failed to clear core instructions")
                return 1

        elif args.command == "core-list":
            presets = manager.list_core_presets(args.core_presets_dir)
            if presets:
                print("Available core instruction presets:")
                for preset in presets:
                    print(f"  - {preset}")
                print(f"\nLoad with: python persona_manager.py core-load -f {args.core_presets_dir}/FILENAME")
            else:
                print(f"No core instruction presets found in {args.core_presets_dir}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())