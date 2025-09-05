"""Unit tests for the RestAPI client."""
import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import BaseModel

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.cli.api.endpoints import (
    CREATE_ENDPOINT,
    DEPLOY_ENDPOINT,
    DOCS_ENDPOINT,
    EXPERT_ENDPOINT,
    IDENTIFY_ENDPOINT,
    IMPROVE_ENDPOINT,
    LOOKUP_ENDPOINT,
    PR_LOOKUP_ENDPOINT,
    RUN_ENDPOINT,
    RUN_ON_PR_ENDPOINT,
)
from graph_sitter.cli.api.schemas import (
    AskExpertInput,
    AskExpertResponse,
    CodemodRunType,
    CreateInput,
    CreateResponse,
    DeployInput,
    DeployResponse,
    DocsInput,
    DocsResponse,
    IdentifyResponse,
    ImproveCodemodInput,
    ImproveCodemodResponse,
    LookupInput,
    LookupOutput,
    PRLookupInput,
    PRLookupResponse,
    RunCodemodInput,
    RunCodemodOutput,
    RunOnPRInput,
    RunOnPRResponse,
)
from graph_sitter.cli.auth.session import CliSession
from graph_sitter.cli.errors import InvalidTokenError, ServerError
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


@pytest.fixture
def mock_session(monkeypatch):
    """Mock the requests.Session to avoid actual HTTP requests."""
    mock_session = MagicMock(spec=requests.Session)
    monkeypatch.setattr("graph_sitter.cli.api.client.requests.Session", lambda: mock_session)
    return mock_session


@pytest.fixture
def api_client():
    """Create a RestAPI client with a test token."""
    return RestAPI(auth_token="test_token")


@pytest.fixture
def mock_cli_session(monkeypatch):
    """Mock the CliSession to return a test configuration."""
    mock_session = MagicMock(spec=CliSession)
    mock_session.config.repository.full_name = "test/repo"
    mock_session.config.repository.language = "python"
    monkeypatch.setattr("graph_sitter.cli.api.client.CliSession.from_active_session", lambda: mock_session)
    return mock_session


class TestRestAPIAuthentication:
    """Test authentication handling in the RestAPI client."""

    def test_auth_headers(self, api_client):
        """Test that authentication headers are correctly set."""
        headers = api_client._get_headers()
        assert headers["Authorization"] == "Bearer test_token"


class TestRestAPIRequestHandling:
    """Test the request handling in the RestAPI client."""

    def test_successful_request(self, api_client, mock_session):
        """Test handling of a successful request."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_session.request.return_value = mock_response

        # Define test models
        class TestInput(BaseModel):
            test_field: str

        class TestOutput(BaseModel):
            success: bool

        # Make request
        result = api_client._make_request(
            "GET",
            "https://test.endpoint",
            TestInput(test_field="test"),
            TestOutput,
        )

        # Verify request was made correctly
        mock_session.request.assert_called_once_with(
            "GET",
            "https://test.endpoint",
            json={"test_field": "test"},
            headers={"Authorization": "Bearer test_token"},
        )

        # Verify response was parsed correctly
        assert isinstance(result, TestOutput)
        assert result.success is True

    def test_unauthorized_request(self, api_client, mock_session):
        """Test handling of a 401 unauthorized response."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_session.request.return_value = mock_response

        # Define test models
        class TestInput(BaseModel):
            test_field: str

        class TestOutput(BaseModel):
            success: bool

        # Make request and verify exception
        with pytest.raises(InvalidTokenError, match="Invalid or expired authentication token"):
            api_client._make_request(
                "GET",
                "https://test.endpoint",
                TestInput(test_field="test"),
                TestOutput,
            )

    def test_server_error(self, api_client, mock_session):
        """Test handling of a 500 server error response."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_session.request.return_value = mock_response

        # Define test models
        class TestInput(BaseModel):
            test_field: str

        class TestOutput(BaseModel):
            success: bool

        # Make request and verify exception
        with pytest.raises(ServerError, match="The server encountered an error while processing your request"):
            api_client._make_request(
                "GET",
                "https://test.endpoint",
                TestInput(test_field="test"),
                TestOutput,
            )

    def test_other_error_with_json(self, api_client, mock_session):
        """Test handling of other error responses with JSON details."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Bad request"}
        mock_session.request.return_value = mock_response

        # Define test models
        class TestInput(BaseModel):
            test_field: str

        class TestOutput(BaseModel):
            success: bool

        # Make request and verify exception
        with pytest.raises(ServerError, match="Error \\(400\\): Bad request"):
            api_client._make_request(
                "GET",
                "https://test.endpoint",
                TestInput(test_field="test"),
                TestOutput,
            )

    def test_network_error(self, api_client, mock_session):
        """Test handling of network errors."""
        # Setup mock to raise an exception
        mock_session.request.side_effect = requests.RequestException("Connection error")

        # Define test models
        class TestInput(BaseModel):
            test_field: str

        class TestOutput(BaseModel):
            success: bool

        # Make request and verify exception
        with pytest.raises(ServerError, match="Network error: Connection error"):
            api_client._make_request(
                "GET",
                "https://test.endpoint",
                TestInput(test_field="test"),
                TestOutput,
            )


class TestRunEndpoint:
    """Test the run endpoint."""

    def test_run_with_source(self, api_client, mock_session, mock_cli_session):
        """Test running a codemod with source code."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "web_link": "https://example.com/run/123",
            "logs": "Codemod executed successfully",
            "observation": "Changes applied",
            "error": None,
        }
        mock_session.request.return_value = mock_response

        # Mock function
        mock_function = MagicMock()
        mock_function.name = "test_codemod"
        mock_function.source = "def test_codemod(): pass"

        # Run the codemod
        result = api_client.run(mock_function, include_source=True)

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "POST"
        assert args[1] == RUN_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "input" in request_data
        assert request_data["input"]["codemod_name"] == "test_codemod"
        assert request_data["input"]["repo_full_name"] == "test/repo"
        assert request_data["input"]["codemod_source"] == "def test_codemod(): pass"

        # Verify response was parsed correctly
        assert isinstance(result, RunCodemodOutput)
        assert result.success is True
        assert result.web_link == "https://example.com/run/123"
        assert result.logs == "Codemod executed successfully"
        assert result.observation == "Changes applied"
        assert result.error is None

    def test_run_without_source(self, api_client, mock_session, mock_cli_session):
        """Test running a codemod without source code (using deployed version)."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "web_link": "https://example.com/run/123",
            "logs": "Codemod executed successfully",
            "observation": "Changes applied",
            "error": None,
        }
        mock_session.request.return_value = mock_response

        # Mock function
        mock_function = MagicMock()
        mock_function.name = "test_codemod"
        mock_function.source = "def test_codemod(): pass"

        # Run the codemod
        result = api_client.run(mock_function, include_source=False)

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "POST"
        assert args[1] == RUN_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "input" in request_data
        assert request_data["input"]["codemod_name"] == "test_codemod"
        assert request_data["input"]["repo_full_name"] == "test/repo"
        assert "codemod_source" not in request_data["input"]

        # Verify response was parsed correctly
        assert isinstance(result, RunCodemodOutput)
        assert result.success is True


class TestDocsEndpoint:
    """Test the docs endpoint."""

    def test_get_docs(self, api_client, mock_session, mock_cli_session):
        """Test getting documentation."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "docs": {"test_doc": "Test documentation"},
            "examples": [],
            "language": "python",
        }
        mock_session.request.return_value = mock_response

        # Get docs
        result = api_client.get_docs()

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "GET"
        assert args[1] == DOCS_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "docs_input" in request_data
        assert request_data["docs_input"]["repo_full_name"] == "test/repo"

        # Verify response was parsed correctly
        assert isinstance(result, DocsResponse)
        assert result.docs == {"test_doc": "Test documentation"}
        assert result.examples == []
        assert result.language == ProgrammingLanguage.PYTHON


class TestExpertEndpoint:
    """Test the expert endpoint."""

    def test_ask_expert(self, api_client, mock_session):
        """Test asking the expert system a question."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is the expert's answer",
            "success": True,
        }
        mock_session.request.return_value = mock_response

        # Ask expert
        result = api_client.ask_expert("How do I create a codemod?")

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "GET"
        assert args[1] == EXPERT_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "input" in request_data
        assert request_data["input"]["query"] == "How do I create a codemod?"

        # Verify response was parsed correctly
        assert isinstance(result, AskExpertResponse)
        assert result.response == "This is the expert's answer"
        assert result.success is True


class TestCreateEndpoint:
    """Test the create endpoint."""

    def test_create(self, api_client, mock_session, mock_cli_session):
        """Test creating a codemod."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "codemod": "def test_codemod(): pass",
            "success": True,
        }
        mock_session.request.return_value = mock_response

        # Create codemod
        result = api_client.create("test_codemod", "Create a test codemod")

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "GET"
        assert args[1] == CREATE_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "input" in request_data
        assert request_data["input"]["name"] == "test_codemod"
        assert request_data["input"]["query"] == "Create a test codemod"
        assert request_data["input"]["language"] == ProgrammingLanguage.PYTHON

        # Verify response was parsed correctly
        assert isinstance(result, CreateResponse)
        assert result.codemod == "def test_codemod(): pass"
        assert result.success is True


class TestIdentifyEndpoint:
    """Test the identify endpoint."""

    def test_identify(self, api_client, mock_session):
        """Test identifying a codemod."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "codemod_name": "test_codemod",
            "success": True,
        }
        mock_session.request.return_value = mock_response

        # Identify codemod
        result = api_client.identify()

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "POST"
        assert args[1] == IDENTIFY_ENDPOINT
        assert kwargs["json"] is None

        # Verify response was parsed correctly
        assert isinstance(result, IdentifyResponse)
        assert result.codemod_name == "test_codemod"
        assert result.success is True


class TestDeployEndpoint:
    """Test the deploy endpoint."""

    def test_deploy(self, api_client, mock_session, mock_cli_session):
        """Test deploying a codemod."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "codemod_id": 123,
        }
        mock_session.request.return_value = mock_response

        # Deploy codemod
        result = api_client.deploy(
            codemod_name="test_codemod",
            codemod_source="def test_codemod(): pass",
            lint_mode=True,
            lint_user_whitelist=["user1", "user2"],
            message="Test deployment",
            arguments_schema={"arg1": {"type": "string"}},
        )

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "POST"
        assert args[1] == DEPLOY_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "input" in request_data
        assert request_data["input"]["codemod_name"] == "test_codemod"
        assert request_data["input"]["codemod_source"] == "def test_codemod(): pass"
        assert request_data["input"]["repo_full_name"] == "test/repo"
        assert request_data["input"]["lint_mode"] is True
        assert request_data["input"]["lint_user_whitelist"] == ["user1", "user2"]
        assert request_data["input"]["message"] == "Test deployment"
        assert request_data["input"]["arguments_schema"] == {"arg1": {"type": "string"}}

        # Verify response was parsed correctly
        assert isinstance(result, DeployResponse)
        assert result.success is True
        assert result.codemod_id == 123


class TestLookupEndpoint:
    """Test the lookup endpoint."""

    def test_lookup(self, api_client, mock_session, mock_cli_session):
        """Test looking up a codemod."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "codemod": {
                "id": 123,
                "name": "test_codemod",
                "source": "def test_codemod(): pass",
            },
        }
        mock_session.request.return_value = mock_response

        # Lookup codemod
        result = api_client.lookup("test_codemod")

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "GET"
        assert args[1] == LOOKUP_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "input" in request_data
        assert request_data["input"]["codemod_name"] == "test_codemod"
        assert request_data["input"]["repo_full_name"] == "test/repo"

        # Verify response was parsed correctly
        assert isinstance(result, LookupOutput)
        assert result.success is True
        assert result.codemod.id == 123
        assert result.codemod.name == "test_codemod"
        assert result.codemod.source == "def test_codemod(): pass"


class TestRunOnPREndpoint:
    """Test the run_on_pr endpoint."""

    def test_run_on_pr(self, api_client, mock_session):
        """Test running a codemod on a PR."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "pr_number": 123,
            "repo_full_name": "test/repo",
        }
        mock_session.request.return_value = mock_response

        # Run on PR
        result = api_client.run_on_pr(
            codemod_name="test_codemod",
            repo_full_name="test/repo",
            github_pr_number=123,
            language="python",
        )

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "POST"
        assert args[1] == RUN_ON_PR_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "input" in request_data
        assert request_data["input"]["codemod_name"] == "test_codemod"
        assert request_data["input"]["repo_full_name"] == "test/repo"
        assert request_data["input"]["github_pr_number"] == 123
        assert request_data["input"]["language"] == "python"

        # Verify response was parsed correctly
        assert isinstance(result, RunOnPRResponse)
        assert result.success is True
        assert result.pr_number == 123
        assert result.repo_full_name == "test/repo"


class TestPRLookupEndpoint:
    """Test the pr_lookup endpoint."""

    def test_lookup_pr(self, api_client, mock_session):
        """Test looking up a PR."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "pr_number": 123,
            "repo_full_name": "test/repo",
            "status": "completed",
        }
        mock_session.request.return_value = mock_response

        # Lookup PR
        result = api_client.lookup_pr("test/repo", 123)

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "GET"
        assert args[1] == PR_LOOKUP_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "input" in request_data
        assert request_data["input"]["repo_full_name"] == "test/repo"
        assert request_data["input"]["github_pr_number"] == 123

        # Verify response was parsed correctly
        assert isinstance(result, PRLookupResponse)
        assert result.success is True
        assert result.pr_number == 123
        assert result.repo_full_name == "test/repo"
        assert result.status == "completed"


class TestImproveCodemodEndpoint:
    """Test the improve_codemod endpoint."""

    def test_improve_codemod(self, api_client, mock_session):
        """Test improving a codemod."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "improved_codemod": "def improved_codemod(): pass",
        }
        mock_session.request.return_value = mock_response

        # Improve codemod
        result = api_client.improve_codemod(
            codemod="def test_codemod(): pass",
            task="Improve error handling",
            concerns=["error_handling", "performance"],
            context={"file_type": "python"},
            language=ProgrammingLanguage.PYTHON,
        )

        # Verify request was made correctly
        mock_session.request.assert_called_once()
        args, kwargs = mock_session.request.call_args
        assert args[0] == "GET"
        assert args[1] == IMPROVE_ENDPOINT
        assert "json" in kwargs
        request_data = kwargs["json"]
        assert "input" in request_data
        assert request_data["input"]["codemod"] == "def test_codemod(): pass"
        assert request_data["input"]["task"] == "Improve error handling"
        assert request_data["input"]["concerns"] == ["error_handling", "performance"]
        assert request_data["input"]["context"] == {"file_type": "python"}
        assert request_data["input"]["language"] == ProgrammingLanguage.PYTHON

        # Verify response was parsed correctly
        assert isinstance(result, ImproveCodemodResponse)
        assert result.success is True
        assert result.improved_codemod == "def improved_codemod(): pass"

