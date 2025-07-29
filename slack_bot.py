"""
Slack Bot Integration for Agent Platform
Connects the Redis-backed chat agent to Slack channels and DMs
"""

import os
import re
import logging
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from dotenv import load_dotenv
from app import agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class SlackAgent:
    def __init__(self):
        self.slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.slack_app_token = os.getenv("SLACK_APP_TOKEN")
        
        logger.info(f"Bot token present: {bool(self.slack_bot_token)}")
        logger.info(f"App token present: {bool(self.slack_app_token)}")
        
        if not self.slack_bot_token or not self.slack_app_token:
            raise ValueError("SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set in environment")
        
        self.client = WebClient(token=self.slack_bot_token)
        self.socket_client = SocketModeClient(
            app_token=self.slack_app_token,
            web_client=self.client
        )
        
        # Get bot user ID for mention detection
        try:
            auth_response = self.client.auth_test()
            self.bot_user_id = auth_response["user_id"]
            logger.info(f"Slack bot initialized as user ID: {self.bot_user_id}")
            logger.info(f"Bot user name: {auth_response.get('user', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error getting bot user ID: {e}")
            raise

    def start(self):
        """Start the Slack bot"""
        self.socket_client.socket_mode_request_listeners.append(self.handle_message)
        logger.info("Starting Slack bot...")
        try:
            self.socket_client.connect()
            logger.info("Slack bot connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Slack: {e}")
            raise

    def handle_message(self, client: SocketModeClient, req: SocketModeRequest):
        """Handle incoming Slack messages"""
        try:
            logger.info(f"Received request type: {req.type}")
            logger.debug(f"Request payload: {req.payload}")
            
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)
            logger.debug("Request acknowledged")
            
            if req.type == "events_api":
                event = req.payload.get("event", {})
                logger.info(f"Event type: {event.get('type')}")
                logger.info(f"Event details: channel={event.get('channel')}, user={event.get('user')}, text='{event.get('text', '')[:50]}...'")
                
                # Only handle message events
                if event.get("type") != "message":
                    logger.info(f"Ignoring non-message event: {event.get('type')}")
                    return
                
                # Skip bot messages and message changes
                subtype = event.get("subtype")
                if subtype in ["bot_message", "message_changed", "message_deleted"]:
                    logger.info(f"Ignoring message subtype: {subtype}")
                    return
                
                # Skip messages from this bot
                if event.get("user") == self.bot_user_id:
                    logger.info("Ignoring message from bot itself")
                    return
                
                channel = event.get("channel")
                user_id = event.get("user")
                text = event.get("text", "")
                thread_ts = event.get("thread_ts") or event.get("ts")
                channel_type = event.get("channel_type")
                
                logger.info(f"Processing message: channel={channel}, user={user_id}, channel_type={channel_type}")
                
                # Check if bot is mentioned or it's a DM
                should_respond = self._should_respond(event, text)
                logger.info(f"Should respond: {should_respond}")
                
                if should_respond and text.strip():
                    logger.info(f"Processing message from user {user_id}: '{text[:100]}...'")
                    
                    # Clean the message text (remove mentions)
                    clean_text = self._clean_message_text(text)
                    logger.info(f"Cleaned text: '{clean_text[:100]}...'")
                    
                    # Use user_id as the unique identifier for chat history
                    uid = f"slack_{user_id}"
                    
                    # Get agent response
                    logger.info(f"Calling agent with uid: {uid}")
                    agent_response = agent(uid, clean_text)
                    logger.info(f"Agent response: '{agent_response[:100]}...'")
                    
                    # Send response to Slack
                    self._send_response(channel, agent_response, thread_ts)
                elif not text.strip():
                    logger.info("Ignoring empty message")
                else:
                    logger.info("Bot should not respond to this message")
            else:
                logger.info(f"Ignoring non-events_api request: {req.type}")
                    
        except Exception as e:
            logger.error(f"Error handling Slack message: {e}", exc_info=True)

    def _should_respond(self, event, text):
        """Determine if the bot should respond to this message"""
        channel_type = event.get("channel_type")
        channel = event.get("channel", "")
        
        logger.info(f"Checking if should respond: channel_type={channel_type}, channel={channel}")
        
        # Always respond to DMs
        if channel_type == "im":
            logger.info("Responding to DM")
            return True
        
        # Check if channel starts with 'D' (DM channel ID format)
        if channel.startswith('D'):
            logger.info("Responding to DM (channel ID format)")
            return True
        
        # In channels, only respond if mentioned
        mention_pattern = f"<@{self.bot_user_id}>"
        if mention_pattern in text:
            logger.info(f"Responding to mention: {mention_pattern}")
            return True
        
        logger.info("Not responding to this message")
        return False

    def _clean_message_text(self, text):
        """Remove bot mentions and clean up message text"""
        # Remove bot mention
        text = re.sub(f"<@{self.bot_user_id}>", "", text)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _send_response(self, channel, response, thread_ts=None):
        """Send response back to Slack"""
        try:
            logger.info(f"Sending response to channel {channel}: '{response[:100]}...'")
            result = self.client.chat_postMessage(
                channel=channel,
                text=response,
                thread_ts=thread_ts  # Reply in thread if available
            )
            logger.info(f"Message sent successfully: {result.get('ok', False)}")
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}", exc_info=True)

def main():
    """Main function to run the Slack bot"""
    try:
        logger.info("Initializing Slack agent...")
        slack_agent = SlackAgent()
        slack_agent.start()
    except KeyboardInterrupt:
        logger.info("\nShutting down Slack bot...")
    except Exception as e:
        logger.error(f"Error starting Slack bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()