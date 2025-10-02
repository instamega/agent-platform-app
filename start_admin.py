#!/usr/bin/env python3
"""
Startup script for Agent Platform Admin Panel
Provides easy way to launch the web GUI with proper configuration
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

def setup_logging(debug=False):
    """Configure logging"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = {
        'flask': 'flask',
        'redis': 'redis', 
        'python-dotenv': 'dotenv',  # Special case: package name vs import name
        'redisvl': 'redisvl',
        'langchain-openai': 'langchain_openai',
        'langchain-community': 'langchain_community'
    }
    
    missing_packages = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_redis_connection():
    """Check Redis connection"""
    try:
        from redis import Redis
        
        client = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
        
        client.ping()
        print("✅ Redis connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Redis Stack is running:")
        print("   docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest")
        print("2. Check your .env file for correct Redis configuration")
        print("3. Verify Redis is accessible at the configured host/port")
        return False

def check_environment():
    """Check environment configuration"""
    required_env_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for agent functionality'
    }
    
    optional_env_vars = {
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'REDIS_PASSWORD': None,
        'FLASK_SECRET_KEY': 'dev-key (change in production)'
    }
    
    issues = []
    
    # Check required variables
    for var, description in required_env_vars.items():
        if not os.getenv(var):
            issues.append(f"❌ Missing required environment variable: {var} ({description})")
        else:
            print(f"✅ {var} is configured")
    
    # Check optional variables
    for var, default in optional_env_vars.items():
        value = os.getenv(var, default)
        if value:
            # Don't show actual API keys for security
            display_value = "***" if "KEY" in var and len(value) > 10 else value
            print(f"ℹ️  {var} = {display_value}")
        else:
            print(f"⚠️  {var} not set (will use default: {default})")
    
    if issues:
        print("\n".join(issues))
        print("\nCreate a .env file with the required configuration:")
        print("OPENAI_API_KEY=your_api_key_here")
        return False
    
    return True

def start_admin_panel(host='localhost', port=5000, debug=False):
    """Start the admin panel"""
    try:
        from admin_panel import app
        
        print(f"\n🚀 Starting Agent Platform Admin Panel...")
        print(f"📍 Access URL: http://{host}:{port}")
        print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
        print(f"\n📊 Available features:")
        print(f"   • System Dashboard - Monitor agent performance")
        print(f"   • Persona Management - Configure agent personality")
        print(f"   • Memory Graph - View and manage knowledge graph")
        print(f"   • Conversations - Browse chat history")
        print(f"   • Knowledge Base - Manage documents")
        print(f"   • System Configuration - Health monitoring")
        print(f"\nPress Ctrl+C to stop the server\n")
        
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 Admin panel stopped by user")
    except Exception as e:
        print(f"❌ Failed to start admin panel: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Agent Platform Admin Panel")
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--skip-checks', action='store_true', help='Skip dependency and connection checks')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging(args.debug)
    
    print("🤖 Agent Platform Admin Panel Startup")
    print("=" * 40)
    
    if not args.skip_checks:
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Check environment
        if not check_environment():
            sys.exit(1)
        
        # Check Redis connection
        if not check_redis_connection():
            sys.exit(1)
        
        print("\n✅ All checks passed!")
    else:
        print("⚠️  Skipping startup checks")
    
    # Start the admin panel
    start_admin_panel(args.host, args.port, args.debug)

if __name__ == "__main__":
    main()