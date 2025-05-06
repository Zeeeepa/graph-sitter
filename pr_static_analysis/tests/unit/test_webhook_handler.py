import unittest
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pr_static_analysis.webhook import WebhookHandler

class TestWebhookHandler(unittest.TestCase):
    def setUp(self):
        # Create a FastAPI app for testing
        self.app = FastAPI()
        
        # Create a webhook handler
        self.webhook_handler = WebhookHandler()
        
        # Define a test handler function
        def test_handler(payload):
            return {"status": "processed", "event": payload.get("type")}
        
        # Register the handler
        self.webhook_handler.register_handler("pull_request", test_handler)
        
        # Define the webhook endpoint
        @self.app.post("/webhook")
        async def webhook(request):
            return await self.webhook_handler.handle_webhook(request)
        
        # Create a test client
        self.client = TestClient(self.app)
    
    def test_register_handler(self):
        # Test registering a handler
        def another_handler(payload):
            return {"status": "processed"}
        
        self.webhook_handler.register_handler("push", another_handler)
        
        self.assertIn("push", self.webhook_handler.event_handlers)
        self.assertEqual(len(self.webhook_handler.event_handlers["push"]), 1)
    
    def test_validate_event(self):
        # Test validating an event
        valid_payload = {
            "repository": {
                "full_name": "testuser/test-repo"
            }
        }
        
        invalid_payload = {}
        
        self.assertTrue(self.webhook_handler.validate_event(valid_payload))
        self.assertFalse(self.webhook_handler.validate_event(invalid_payload))
    
    def test_webhook_endpoint(self):
        # Test the webhook endpoint
        payload = {
            "type": "pull_request",
            "action": "opened",
            "repository": {
                "full_name": "testuser/test-repo"
            }
        }
        
        response = self.client.post(
            "/webhook",
            headers={"X-GitHub-Event": "pull_request"},
            json=payload
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["event"], "pull_request")
        self.assertEqual(response.json()["action"], "opened")

if __name__ == "__main__":
    unittest.main()

