from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

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
    SerializedExample,
)
from graph_sitter.cli.errors import ServerError
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


@pytest.fixture
def api_client():
    """Create a RestAPI client with a mock auth token."""
    return RestAPI(auth_token="mock_token")


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    mock = MagicMock()
    mock.status_code = 200
    return mock


class TestModelConversion:
    """Test model conversion in the RestAPI client."""

    def test_run_codemod_output_conversion(self, api_client, mock_response):
        """Test conversion of JSON to RunCodemodOutput."""
        # Setup mock response
        mock_response.json.return_value = {
            "success": True,
            "web_link": "https://example.com/run/123",
            "logs": "Running codemod...",
            "observation": "Codemod completed successfully",
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "POST",
                "https://example.com/api",
                None,
                RunCodemodOutput,
            )
            
            # Verify the result
            assert isinstance(result, RunCodemodOutput)
            assert result.success is True
            assert result.web_link == "https://example.com/run/123"
            assert result.logs == "Running codemod..."
            assert result.observation == "Codemod completed successfully"

    def test_docs_response_conversion(self, api_client, mock_response):
        """Test conversion of JSON to DocsResponse."""
        # Setup mock response
        mock_response.json.return_value = {
            "docs": {"doc1": "content1", "doc2": "content2"},
            "examples": [
                {
                    "name": "example1",
                    "description": "Example 1 description",
                    "source": "def example1():\n    pass",
                    "language": "python",
                    "docstring": "Example 1 docstring",
                }
            ],
            "language": "python",
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "GET",
                "https://example.com/api",
                None,
                DocsResponse,
            )
            
            # Verify the result
            assert isinstance(result, DocsResponse)
            assert result.docs == {"doc1": "content1", "doc2": "content2"}
            assert len(result.examples) == 1
            assert isinstance(result.examples[0], SerializedExample)
            assert result.examples[0].name == "example1"
            assert result.examples[0].language == ProgrammingLanguage.PYTHON

    def test_ask_expert_response_conversion(self, api_client, mock_response):
        """Test conversion of JSON to AskExpertResponse."""
        # Setup mock response
        mock_response.json.return_value = {
            "response": "Expert response",
            "success": True,
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "GET",
                "https://example.com/api",
                None,
                AskExpertResponse,
            )
            
            # Verify the result
            assert isinstance(result, AskExpertResponse)
            assert result.response == "Expert response"
            assert result.success is True

    def test_create_response_conversion(self, api_client, mock_response):
        """Test conversion of JSON to CreateResponse."""
        # Setup mock response
        mock_response.json.return_value = {
            "success": True,
            "response": "Creation response",
            "code": "def example():\n    pass",
            "context": "Example context",
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "GET",
                "https://example.com/api",
                None,
                CreateResponse,
            )
            
            # Verify the result
            assert isinstance(result, CreateResponse)
            assert result.success is True
            assert result.response == "Creation response"
            assert result.code == "def example():\n    pass"
            assert result.context == "Example context"

    def test_identify_response_conversion(self, api_client, mock_response):
        """Test conversion of JSON to IdentifyResponse."""
        # Setup mock response
        mock_response.json.return_value = {
            "auth_context": {
                "token_id": 123,
                "expires_at": "2023-01-01T00:00:00Z",
                "status": "active",
                "user_id": 456,
            },
            "user": {
                "github_user_id": "789",
                "avatar_url": "https://example.com/avatar.png",
                "auth_user_id": "auth123",
                "created_at": "2022-01-01T00:00:00Z",
                "email": "user@example.com",
                "is_contractor": None,
                "github_username": "username",
                "full_name": "User Name",
                "id": 456,
                "last_updated_at": "2022-12-31T00:00:00Z",
            },
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "POST",
                "https://example.com/api",
                None,
                IdentifyResponse,
            )
            
            # Verify the result
            assert isinstance(result, IdentifyResponse)
            assert result.auth_context.token_id == 123
            assert result.auth_context.user_id == 456
            assert result.user.github_username == "username"
            assert result.user.email == "user@example.com"

    def test_deploy_response_conversion(self, api_client, mock_response):
        """Test conversion of JSON to DeployResponse."""
        # Setup mock response
        mock_response.json.return_value = {
            "success": True,
            "new": True,
            "codemod_id": 123,
            "version_id": 456,
            "url": "https://example.com/codemod/123",
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "POST",
                "https://example.com/api",
                None,
                DeployResponse,
            )
            
            # Verify the result
            assert isinstance(result, DeployResponse)
            assert result.success is True
            assert result.new is True
            assert result.codemod_id == 123
            assert result.version_id == 456
            assert result.url == "https://example.com/codemod/123"

    def test_lookup_output_conversion(self, api_client, mock_response):
        """Test conversion of JSON to LookupOutput."""
        # Setup mock response
        mock_response.json.return_value = {
            "codemod_id": 123,
            "version_id": 456,
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "GET",
                "https://example.com/api",
                None,
                LookupOutput,
            )
            
            # Verify the result
            assert isinstance(result, LookupOutput)
            assert result.codemod_id == 123
            assert result.version_id == 456

    def test_run_on_pr_response_conversion(self, api_client, mock_response):
        """Test conversion of JSON to RunOnPRResponse."""
        # Setup mock response
        mock_response.json.return_value = {
            "codemod_id": 123,
            "codemod_run_id": 456,
            "web_url": "https://example.com/run/456",
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "POST",
                "https://example.com/api",
                None,
                RunOnPRResponse,
            )
            
            # Verify the result
            assert isinstance(result, RunOnPRResponse)
            assert result.codemod_id == 123
            assert result.codemod_run_id == 456
            assert result.web_url == "https://example.com/run/456"

    def test_pr_lookup_response_conversion(self, api_client, mock_response):
        """Test conversion of JSON to PRLookupResponse."""
        # Setup mock response
        mock_response.json.return_value = {
            "pr": {
                "url": "https://github.com/test/repo/pull/123",
                "title": "Example PR",
                "body": "PR description",
                "github_pr_number": 123,
                "codegen_pr_id": 456,
            }
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "GET",
                "https://example.com/api",
                None,
                PRLookupResponse,
            )
            
            # Verify the result
            assert isinstance(result, PRLookupResponse)
            assert result.pr.url == "https://github.com/test/repo/pull/123"
            assert result.pr.title == "Example PR"
            assert result.pr.body == "PR description"
            assert result.pr.github_pr_number == 123
            assert result.pr.codegen_pr_id == 456

    def test_improve_codemod_response_conversion(self, api_client, mock_response):
        """Test conversion of JSON to ImproveCodemodResponse."""
        # Setup mock response
        mock_response.json.return_value = {
            "success": True,
            "codemod_source": "def improved_codemod():\n    print('Improved')",
        }
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request
            result = api_client._make_request(
                "GET",
                "https://example.com/api",
                None,
                ImproveCodemodResponse,
            )
            
            # Verify the result
            assert isinstance(result, ImproveCodemodResponse)
            assert result.success is True
            assert result.codemod_source == "def improved_codemod():\n    print('Improved')"

    def test_invalid_model_conversion(self, api_client, mock_response):
        """Test conversion of JSON to an invalid model."""
        # Setup mock response with invalid data
        mock_response.json.return_value = {
            "invalid_field": "value",
        }
        
        # Define a model with a required field
        class TestModel(RunCodemodOutput):
            required_field: str
        
        # Mock the session to return the response
        with patch.object(api_client._session, "request", return_value=mock_response):
            # Make the request and verify it raises the correct exception
            with pytest.raises(ServerError, match="Invalid response format"):
                api_client._make_request(
                    "GET",
                    "https://example.com/api",
                    None,
                    TestModel,
                )

