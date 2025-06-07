"""
Slack Extension for Contexten

Provides Slack integration with webhook handling and message processing.
"""

from .slack import Slack
from .types import SlackWebhookPayload, SlackMessage, SlackUser, SlackChannel

__version__ = "1.0.0"
__all__ = [
    "Slack",
    "SlackWebhookPayload", 
    "SlackMessage",
    "SlackUser",
    "SlackChannel"
]

