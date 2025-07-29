#!/usr/bin/env python3
"""
Slack Bot Connection Diagnostic Tool
Tests each step of the Slack Socket Mode connection
"""

import os
import logging
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from dotenv import load_dotenv

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment():
    """Test environment variables"""
    logger.info("=== Testing Environment Variables ===")
    
    load_dotenv()
    
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    app_token = os.getenv("SLACK_APP_TOKEN")
    
    if not bot_token:
        logger.error("❌ SLACK_BOT_TOKEN not found")
        return False
    
    if not app_token:
        logger.error("❌ SLACK_APP_TOKEN not found")
        return False
    
    logger.info(f"✅ SLACK_BOT_TOKEN: {bot_token[:10]}...{bot_token[-4:]}")
    logger.info(f"✅ SLACK_APP_TOKEN: {app_token[:10]}...{app_token[-4:]}")
    
    # Validate token formats
    if not bot_token.startswith("xoxb-"):
        logger.error("❌ SLACK_BOT_TOKEN should start with 'xoxb-'")
        return False
        
    if not app_token.startswith("xapp-"):
        logger.error("❌ SLACK_APP_TOKEN should start with 'xapp-'")
        return False
    
    logger.info("✅ Token formats look correct")
    return True

def test_web_client():
    """Test basic Slack Web API connection"""
    logger.info("=== Testing Web API Connection ===")
    
    try:
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        response = client.auth_test()
        
        if response["ok"]:
            logger.info(f"✅ Web API connection successful")
            logger.info(f"   Bot User ID: {response['user_id']}")
            logger.info(f"   Bot User: {response['user']}")
            logger.info(f"   Team: {response['team']}")
            return True, response
        else:
            logger.error(f"❌ Web API auth failed: {response}")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ Web API connection failed: {e}")
        return False, None

def test_socket_connection():
    """Test Socket Mode connection"""
    logger.info("=== Testing Socket Mode Connection ===")
    
    try:
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        socket_client = SocketModeClient(
            app_token=os.getenv("SLACK_APP_TOKEN"),
            web_client=client
        )
        
        logger.info("✅ Socket Mode client created")
        
        # Test connection
        logger.info("Attempting Socket Mode connection...")
        socket_client.connect()
        logger.info("✅ Socket Mode connected successfully!")
        
        # Disconnect after test
        socket_client.disconnect()
        logger.info("✅ Socket Mode disconnected cleanly")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Socket Mode connection failed: {e}")
        return False

def test_app_permissions():
    """Check if app has required permissions"""
    logger.info("=== Testing App Permissions ===")
    
    try:
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        # Test if we can access conversations
        try:
            client.conversations_list(limit=1)
            logger.info("✅ Can access conversations")
        except Exception as e:
            logger.warning(f"⚠️  Cannot access conversations: {e}")
        
        # Test auth scopes
        auth_response = client.auth_test()
        if "scopes" in auth_response:
            scopes = auth_response["scopes"]
            logger.info(f"✅ Bot scopes: {scopes}")
            
            required_scopes = ["chat:write", "app_mentions:read", "im:read", "im:write"]
            missing_scopes = [scope for scope in required_scopes if scope not in scopes]
            
            if missing_scopes:
                logger.error(f"❌ Missing required scopes: {missing_scopes}")
                return False
            else:
                logger.info("✅ All required scopes present")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Permission check failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    logger.info("🔍 Starting Slack Bot Diagnostics")
    logger.info("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment),
        ("Web API Connection", lambda: test_web_client()[0]),
        ("Socket Mode Connection", test_socket_connection),
        ("App Permissions", test_app_permissions),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
        
        logger.info("-" * 30)
    
    # Summary
    logger.info("=== DIAGNOSTIC SUMMARY ===")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed! Your Slack bot should work.")
        logger.info("Try running: python slack_bot.py")
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        
        # Common fixes
        logger.info("🔧 COMMON FIXES:")
        if not results.get("Environment Variables", True):
            logger.info("- Check your .env file has SLACK_BOT_TOKEN and SLACK_APP_TOKEN")
        if not results.get("Web API Connection", True):
            logger.info("- Verify your bot token is correct")
            logger.info("- Check if the Slack app is installed in your workspace")
        if not results.get("Socket Mode Connection", True):
            logger.info("- Ensure Socket Mode is enabled in your Slack app settings")
            logger.info("- Verify your app token has 'connections:write' scope")
        if not results.get("App Permissions", True):
            logger.info("- Add required bot scopes in OAuth settings")
            logger.info("- Reinstall the app to your workspace after adding scopes")

if __name__ == "__main__":
    main()