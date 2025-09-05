from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from graph_sitter.cli.api.client import RestAPI
from graph_sitter.cli.api.schemas import (
    AskExpertInput,
    CodemodRunType,
    CreateInput,
    DeployInput,
    DocsInput,
    ImproveCodemodInput,
    LookupInput,
    PRLookupInput,
    RunCodemodInput,
    RunOnPRInput,
)
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


@pytest.fixture
def api_client():
    """Create a RestAPI client with a mock auth token."""
    return RestAPI(auth_token="mock_token")


@pytest.fixture
def mock_session_config():
    """Mock the CliSession configuration."""
    with patch("graph_sitter.cli.api.client.CliSession") as mock_session:
        mock_session.from_active_session.return_value.config.repository.full_name = "test/repo"
        mock_session.from_active_session.return_value.config.repository.language = "python"
        yield mock_session


class TestInputValidation:
    """Test input validation in the RestAPI client."""

    def test_run_input_validation(self, api_client, mock_session_config):
        """Test validation of run input."""
        # Create a mock codemod
        mock_codemod = MagicMock()
        mock_codemod.name = "test_codemod"
        mock_codemod.get_current_source.return_value = "def test_codemod():\n    pass"
        
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run the codemod
            api_client.run(mock_codemod)
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is a valid RunCodemodInput
            assert isinstance(input_data, RunCodemodInput)
            assert input_data.input.codemod_name == "test_codemod"
            assert input_data.input.repo_full_name == "test/repo"
            assert input_data.input.codemod_run_type == CodemodRunType.DIFF
            assert "def test_codemod():" in input_data.input.codemod_source

    def test_get_docs_input_validation(self, api_client, mock_session_config):
        """Test validation of get_docs input."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Get docs
            api_client.get_docs()
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is a valid DocsInput
            assert isinstance(input_data, DocsInput)
            assert input_data.docs_input.repo_full_name == "test/repo"

    def test_ask_expert_input_validation(self, api_client):
        """Test validation of ask_expert input."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Ask expert
            api_client.ask_expert("How do I use graph-sitter?")
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is a valid AskExpertInput
            assert isinstance(input_data, AskExpertInput)
            assert input_data.input.query == "How do I use graph-sitter?"

    def test_create_input_validation(self, api_client, mock_session_config):
        """Test validation of create input."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Create codemod
            api_client.create("example_codemod", "Create a codemod that does X")
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is a valid CreateInput
            assert isinstance(input_data, CreateInput)
            assert input_data.input.name == "example_codemod"
            assert input_data.input.query == "Create a codemod that does X"
            assert input_data.input.language == ProgrammingLanguage.PYTHON

    def test_identify_input_validation(self, api_client):
        """Test validation of identify input."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Identify user
            api_client.identify()
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is None
            assert input_data is None

    def test_deploy_input_validation(self, api_client, mock_session_config):
        """Test validation of deploy input."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Deploy codemod
            api_client.deploy(
                codemod_name="example_codemod",
                codemod_source="def example_codemod():\n    pass",
                lint_mode=True,
                lint_user_whitelist=["user1", "user2"],
                message="Example codemod",
                arguments_schema={"type": "object", "properties": {"arg1": {"type": "string"}}},
            )
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is a valid DeployInput
            assert isinstance(input_data, DeployInput)
            assert input_data.input.codemod_name == "example_codemod"
            assert input_data.input.codemod_source == "def example_codemod():\n    pass"
            assert input_data.input.repo_full_name == "test/repo"
            assert input_data.input.lint_mode is True
            assert input_data.input.lint_user_whitelist == ["user1", "user2"]
            assert input_data.input.message == "Example codemod"
            assert input_data.input.arguments_schema == {"type": "object", "properties": {"arg1": {"type": "string"}}}

    def test_lookup_input_validation(self, api_client, mock_session_config):
        """Test validation of lookup input."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Lookup codemod
            api_client.lookup("example_codemod")
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is a valid LookupInput
            assert isinstance(input_data, LookupInput)
            assert input_data.input.codemod_name == "example_codemod"
            assert input_data.input.repo_full_name == "test/repo"

    def test_run_on_pr_input_validation(self, api_client):
        """Test validation of run_on_pr input."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Run on PR
            api_client.run_on_pr(
                codemod_name="example_codemod",
                repo_full_name="test/repo",
                github_pr_number=123,
                language="python",
            )
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is a valid RunOnPRInput
            assert isinstance(input_data, RunOnPRInput)
            assert input_data.input.codemod_name == "example_codemod"
            assert input_data.input.repo_full_name == "test/repo"
            assert input_data.input.github_pr_number == 123
            assert input_data.input.language == "python"

    def test_lookup_pr_input_validation(self, api_client):
        """Test validation of lookup_pr input."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Lookup PR
            api_client.lookup_pr(
                repo_full_name="test/repo",
                github_pr_number=123,
            )
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is a valid PRLookupInput
            assert isinstance(input_data, PRLookupInput)
            assert input_data.input.repo_full_name == "test/repo"
            assert input_data.input.github_pr_number == 123

    def test_improve_codemod_input_validation(self, api_client):
        """Test validation of improve_codemod input."""
        # Mock the _make_request method to return the input data
        with patch.object(api_client, "_make_request") as mock_make_request:
            # Improve codemod
            api_client.improve_codemod(
                codemod="def original_codemod():\n    pass",
                task="Improve the codemod to print something",
                concerns=["Doesn't do anything"],
                context={"file1.py": "def example():\n    pass"},
                language=ProgrammingLanguage.PYTHON,
            )
            
            # Verify the input data
            mock_make_request.assert_called_once()
            call_args = mock_make_request.call_args[0]
            input_data = call_args[2]
            
            # Verify the input data is a valid ImproveCodemodInput
            assert isinstance(input_data, ImproveCodemodInput)
            assert input_data.input.codemod == "def original_codemod():\n    pass"
            assert input_data.input.task == "Improve the codemod to print something"
            assert input_data.input.concerns == ["Doesn't do anything"]
            assert input_data.input.context == {"file1.py": "def example():\n    pass"}
            assert input_data.input.language == ProgrammingLanguage.PYTHON

    def test_invalid_input_validation(self, api_client):
        """Test validation of invalid input."""
        # Define an invalid input model
        class InvalidInput(BaseModel):
            required_field: str
        
        # Attempt to make a request with an invalid input
        with pytest.raises(ValidationError):
            api_client._make_request(
                "GET",
                "https://example.com/api",
                InvalidInput(),
                MagicMock(),
            )

