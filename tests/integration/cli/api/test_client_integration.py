"""Integration tests for the RestAPI client."""
import json
from unittest.mock import MagicMock, patch

import pytest
import requests
import responses

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
from graph_sitter.cli.errors import InvalidTokenError, ServerError
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


@pytest.fixture
def mock_cli_session(monkeypatch):
    """Mock the CliSession to return a test configuration."""
    mock_session = MagicMock()
    mock_session.config.repository.full_name = "test/repo"
    mock_session.config.repository.language = "python"
    monkeypatch.setattr("graph_sitter.cli.api.client.CliSession.from_active_session", lambda: mock_session)
    return mock_session


@pytest.fixture
def api_client():
    """Create a RestAPI client with a test token."""
    return RestAPI(auth_token="test_token")


@pytest.mark.integration
class TestRestAPIIntegration:
    """Integration tests for the RestAPI client using responses library."""

    @responses.activate
    def test_run_endpoint_success(self, api_client, mock_cli_session):
        """Test successful run endpoint integration."""
        # Mock the function
        mock_function = MagicMock()
        mock_function.name = "test_codemod"
        mock_function.source = "def test_codemod(): pass"

        # Setup mock response
        responses.add(
            responses.POST,
            RUN_ENDPOINT,
            json={
                "success": True,
                "web_link": "https://example.com/run/123",
                "logs": "Codemod executed successfully",
                "observation": "Changes applied",
                "error": None,
            },
            status=200,
        )

        # Run the codemod
        result = api_client.run(mock_function)

        # Verify response
        assert isinstance(result, RunCodemodOutput)
        assert result.success is True
        assert result.web_link == "https://example.com/run/123"
        assert result.logs == "Codemod executed successfully"
        assert result.observation == "Changes applied"
        assert result.error is None

        # Verify request
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert "input" in request_body
        assert request_body["input"]["codemod_name"] == "test_codemod"
        assert request_body["input"]["repo_full_name"] == "test/repo"
        assert request_body["input"]["codemod_source"] == "def test_codemod(): pass"

    @responses.activate
    def test_get_docs_endpoint_success(self, api_client, mock_cli_session):
        """Test successful get_docs endpoint integration."""
        # Setup mock response
        responses.add(
            responses.GET,
            DOCS_ENDPOINT,
            json={
                "docs": {"test_doc": "Test documentation"},
                "examples": [],
                "language": "python",
            },
            status=200,
        )

        # Get docs
        result = api_client.get_docs()

        # Verify response
        assert isinstance(result, DocsResponse)
        assert result.docs == {"test_doc": "Test documentation"}
        assert result.examples == []
        assert result.language == ProgrammingLanguage.PYTHON

        # Verify request
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert "docs_input" in request_body
        assert request_body["docs_input"]["repo_full_name"] == "test/repo"

    @responses.activate
    def test_ask_expert_endpoint_success(self, api_client):
        """Test successful ask_expert endpoint integration."""
        # Setup mock response
        responses.add(
            responses.GET,
            EXPERT_ENDPOINT,
            json={
                "response": "This is the expert's answer",
                "success": True,
            },
            status=200,
        )

        # Ask expert
        result = api_client.ask_expert("How do I create a codemod?")

        # Verify response
        assert isinstance(result, AskExpertResponse)
        assert result.response == "This is the expert's answer"
        assert result.success is True

        # Verify request
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert "input" in request_body
        assert request_body["input"]["query"] == "How do I create a codemod?"

    @responses.activate
    def test_create_endpoint_success(self, api_client, mock_cli_session):
        """Test successful create endpoint integration."""
        # Setup mock response
        responses.add(
            responses.GET,
            CREATE_ENDPOINT,
            json={
                "codemod": "def test_codemod(): pass",
                "success": True,
            },
            status=200,
        )

        # Create codemod
        result = api_client.create("test_codemod", "Create a test codemod")

        # Verify response
        assert isinstance(result, CreateResponse)
        assert result.codemod == "def test_codemod(): pass"
        assert result.success is True

        # Verify request
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert "input" in request_body
        assert request_body["input"]["name"] == "test_codemod"
        assert request_body["input"]["query"] == "Create a test codemod"
        assert request_body["input"]["language"] == ProgrammingLanguage.PYTHON

    @responses.activate
    def test_identify_endpoint_success(self, api_client):
        """Test successful identify endpoint integration."""
        # Setup mock response
        responses.add(
            responses.POST,
            IDENTIFY_ENDPOINT,
            json={
                "codemod_name": "test_codemod",
                "success": True,
            },
            status=200,
        )

        # Identify codemod
        result = api_client.identify()

        # Verify response
        assert isinstance(result, IdentifyResponse)
        assert result.codemod_name == "test_codemod"
        assert result.success is True

        # Verify request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.body is None or responses.calls[0].request.body == b"null"

    @responses.activate
    def test_deploy_endpoint_success(self, api_client, mock_cli_session):
        """Test successful deploy endpoint integration."""
        # Setup mock response
        responses.add(
            responses.POST,
            DEPLOY_ENDPOINT,
            json={
                "success": True,
                "codemod_id": 123,
            },
            status=200,
        )

        # Deploy codemod
        result = api_client.deploy(
            codemod_name="test_codemod",
            codemod_source="def test_codemod(): pass",
        )

        # Verify response
        assert isinstance(result, DeployResponse)
        assert result.success is True
        assert result.codemod_id == 123

        # Verify request
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert "input" in request_body
        assert request_body["input"]["codemod_name"] == "test_codemod"
        assert request_body["input"]["codemod_source"] == "def test_codemod(): pass"
        assert request_body["input"]["repo_full_name"] == "test/repo"

    @responses.activate
    def test_lookup_endpoint_success(self, api_client, mock_cli_session):
        """Test successful lookup endpoint integration."""
        # Setup mock response
        responses.add(
            responses.GET,
            LOOKUP_ENDPOINT,
            json={
                "success": True,
                "codemod": {
                    "id": 123,
                    "name": "test_codemod",
                    "source": "def test_codemod(): pass",
                },
            },
            status=200,
        )

        # Lookup codemod
        result = api_client.lookup("test_codemod")

        # Verify response
        assert isinstance(result, LookupOutput)
        assert result.success is True
        assert result.codemod.id == 123
        assert result.codemod.name == "test_codemod"
        assert result.codemod.source == "def test_codemod(): pass"

        # Verify request
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert "input" in request_body
        assert request_body["input"]["codemod_name"] == "test_codemod"
        assert request_body["input"]["repo_full_name"] == "test/repo"

    @responses.activate
    def test_run_on_pr_endpoint_success(self, api_client):
        """Test successful run_on_pr endpoint integration."""
        # Setup mock response
        responses.add(
            responses.POST,
            RUN_ON_PR_ENDPOINT,
            json={
                "success": True,
                "pr_number": 123,
                "repo_full_name": "test/repo",
            },
            status=200,
        )

        # Run on PR
        result = api_client.run_on_pr(
            codemod_name="test_codemod",
            repo_full_name="test/repo",
            github_pr_number=123,
        )

        # Verify response
        assert isinstance(result, RunOnPRResponse)
        assert result.success is True
        assert result.pr_number == 123
        assert result.repo_full_name == "test/repo"

        # Verify request
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert "input" in request_body
        assert request_body["input"]["codemod_name"] == "test_codemod"
        assert request_body["input"]["repo_full_name"] == "test/repo"
        assert request_body["input"]["github_pr_number"] == 123

    @responses.activate
    def test_lookup_pr_endpoint_success(self, api_client):
        """Test successful lookup_pr endpoint integration."""
        # Setup mock response
        responses.add(
            responses.GET,
            PR_LOOKUP_ENDPOINT,
            json={
                "success": True,
                "pr_number": 123,
                "repo_full_name": "test/repo",
                "status": "completed",
            },
            status=200,
        )

        # Lookup PR
        result = api_client.lookup_pr("test/repo", 123)

        # Verify response
        assert isinstance(result, PRLookupResponse)
        assert result.success is True
        assert result.pr_number == 123
        assert result.repo_full_name == "test/repo"
        assert result.status == "completed"

        # Verify request
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert "input" in request_body
        assert request_body["input"]["repo_full_name"] == "test/repo"
        assert request_body["input"]["github_pr_number"] == 123

    @responses.activate
    def test_improve_codemod_endpoint_success(self, api_client):
        """Test successful improve_codemod endpoint integration."""
        # Setup mock response
        responses.add(
            responses.GET,
            IMPROVE_ENDPOINT,
            json={
                "success": True,
                "improved_codemod": "def improved_codemod(): pass",
            },
            status=200,
        )

        # Improve codemod
        result = api_client.improve_codemod(
            codemod="def test_codemod(): pass",
            task="Improve error handling",
            concerns=["error_handling"],
            context={},
            language=ProgrammingLanguage.PYTHON,
        )

        # Verify response
        assert isinstance(result, ImproveCodemodResponse)
        assert result.success is True
        assert result.improved_codemod == "def improved_codemod(): pass"

        # Verify request
        assert len(responses.calls) == 1
        request_body = json.loads(responses.calls[0].request.body)
        assert "input" in request_body
        assert request_body["input"]["codemod"] == "def test_codemod(): pass"
        assert request_body["input"]["task"] == "Improve error handling"
        assert request_body["input"]["concerns"] == ["error_handling"]
        assert request_body["input"]["language"] == ProgrammingLanguage.PYTHON

    @responses.activate
    def test_error_handling_401(self, api_client):
        """Test error handling for 401 unauthorized responses."""
        # Setup mock response
        responses.add(
            responses.GET,
            EXPERT_ENDPOINT,
            status=401,
        )

        # Make request and verify exception
        with pytest.raises(InvalidTokenError, match="Invalid or expired authentication token"):
            api_client.ask_expert("How do I create a codemod?")

    @responses.activate
    def test_error_handling_500(self, api_client):
        """Test error handling for 500 server error responses."""
        # Setup mock response
        responses.add(
            responses.GET,
            EXPERT_ENDPOINT,
            status=500,
        )

        # Make request and verify exception
        with pytest.raises(ServerError, match="The server encountered an error while processing your request"):
            api_client.ask_expert("How do I create a codemod?")

    @responses.activate
    def test_error_handling_400_with_detail(self, api_client):
        """Test error handling for 400 bad request responses with detail."""
        # Setup mock response
        responses.add(
            responses.GET,
            EXPERT_ENDPOINT,
            json={"detail": "Invalid query parameter"},
            status=400,
        )

        # Make request and verify exception
        with pytest.raises(ServerError, match="Error \\(400\\): Invalid query parameter"):
            api_client.ask_expert("How do I create a codemod?")

    @responses.activate
    def test_network_error(self, api_client):
        """Test error handling for network errors."""
        # Setup mock to raise an exception
        responses.add(
            responses.GET,
            EXPERT_ENDPOINT,
            body=requests.RequestException("Connection error"),
        )

        # Make request and verify exception
        with pytest.raises(ServerError, match="Network error:"):
            api_client.ask_expert("How do I create a codemod?")

