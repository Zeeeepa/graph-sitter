"""
Unit tests for CircleCI extension configuration
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from contexten.extensions.circleci.config import (
    CircleCIIntegrationConfig,
    APIConfig,
    WebhookConfig,
    AutoFixConfig,
    FailureAnalysisConfig,
    WorkflowAutomationConfig,
    NotificationConfig,
    GitHubConfig,
    CodegenConfig
)
