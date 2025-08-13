import inspect
from unittest.mock import patch

import pytest

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.cli.api.schemas import (
    AskExpertResponse,
    CreateResponse,
    DeployResponse,
    DocsResponse,
    IdentifyResponse,
    ImproveCodemodResponse,
    LookupOutput,
    PRLookupResponse,
    RunCodemodOutput,
    RunOnPRResponse,
)
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


@pytest.fixture
def api_client():
    """Create a RestAPI client with a mock auth token."""
    return RestAPI(auth_token="mock_token")


class TestMethodSignatures:
    """Test method signatures in the RestAPI client."""

    def test_run_signature(self, api_client):
        """Test the run method signature."""
        # Get the signature
        sig = inspect.signature(api_client.run)
        
        # Verify the parameters
        assert "function" in sig.parameters
        assert "include_source" in sig.parameters
        assert "run_type" in sig.parameters
        assert "template_context" in sig.parameters
        
        # Verify the return type
        assert sig.return_annotation == RunCodemodOutput

    def test_get_docs_signature(self, api_client):
        """Test the get_docs method signature."""
        # Get the signature
        sig = inspect.signature(api_client.get_docs)
        
        # Verify the parameters
        assert len(sig.parameters) == 0
        
        # Verify the return type
        assert sig.return_annotation == DocsResponse

    def test_ask_expert_signature(self, api_client):
        """Test the ask_expert method signature."""
        # Get the signature
        sig = inspect.signature(api_client.ask_expert)
        
        # Verify the parameters
        assert "query" in sig.parameters
        
        # Verify the return type
        assert sig.return_annotation == AskExpertResponse

    def test_create_signature(self, api_client):
        """Test the create method signature."""
        # Get the signature
        sig = inspect.signature(api_client.create)
        
        # Verify the parameters
        assert "name" in sig.parameters
        assert "query" in sig.parameters
        
        # Verify the return type
        assert sig.return_annotation == CreateResponse

    def test_identify_signature(self, api_client):
        """Test the identify method signature."""
        # Get the signature
        sig = inspect.signature(api_client.identify)
        
        # Verify the parameters
        assert len(sig.parameters) == 0
        
        # Verify the return type
        assert sig.return_annotation == IdentifyResponse

    def test_deploy_signature(self, api_client):
        """Test the deploy method signature."""
        # Get the signature
        sig = inspect.signature(api_client.deploy)
        
        # Verify the parameters
        assert "codemod_name" in sig.parameters
        assert "codemod_source" in sig.parameters
        assert "lint_mode" in sig.parameters
        assert "lint_user_whitelist" in sig.parameters
        assert "message" in sig.parameters
        assert "arguments_schema" in sig.parameters
        
        # Verify the return type
        assert sig.return_annotation == DeployResponse

    def test_lookup_signature(self, api_client):
        """Test the lookup method signature."""
        # Get the signature
        sig = inspect.signature(api_client.lookup)
        
        # Verify the parameters
        assert "codemod_name" in sig.parameters
        
        # Verify the return type
        assert sig.return_annotation == LookupOutput

    def test_run_on_pr_signature(self, api_client):
        """Test the run_on_pr method signature."""
        # Get the signature
        sig = inspect.signature(api_client.run_on_pr)
        
        # Verify the parameters
        assert "codemod_name" in sig.parameters
        assert "repo_full_name" in sig.parameters
        assert "github_pr_number" in sig.parameters
        assert "language" in sig.parameters
        
        # Verify the return type
        assert sig.return_annotation == RunOnPRResponse

    def test_lookup_pr_signature(self, api_client):
        """Test the lookup_pr method signature."""
        # Get the signature
        sig = inspect.signature(api_client.lookup_pr)
        
        # Verify the parameters
        assert "repo_full_name" in sig.parameters
        assert "github_pr_number" in sig.parameters
        
        # Verify the return type
        assert sig.return_annotation == PRLookupResponse

    def test_improve_codemod_signature(self, api_client):
        """Test the improve_codemod method signature."""
        # Get the signature
        sig = inspect.signature(api_client.improve_codemod)
        
        # Verify the parameters
        assert "codemod" in sig.parameters
        assert "task" in sig.parameters
        assert "concerns" in sig.parameters
        assert "context" in sig.parameters
        assert "language" in sig.parameters
        
        # Verify the return type
        assert sig.return_annotation == ImproveCodemodResponse

    def test_make_request_signature(self, api_client):
        """Test the _make_request method signature."""
        # Get the signature
        sig = inspect.signature(api_client._make_request)
        
        # Verify the parameters
        assert "method" in sig.parameters
        assert "endpoint" in sig.parameters
        assert "input_data" in sig.parameters
        assert "output_model" in sig.parameters
        
        # Verify the return type
        assert sig.return_annotation == "OutputT"

    def test_get_headers_signature(self, api_client):
        """Test the _get_headers method signature."""
        # Get the signature
        sig = inspect.signature(api_client._get_headers)
        
        # Verify the parameters
        assert len(sig.parameters) == 0
        
        # Verify the return type
        assert sig.return_annotation == "dict[str, str]"

