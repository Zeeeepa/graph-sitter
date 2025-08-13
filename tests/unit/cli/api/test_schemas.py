"""Unit tests for the API schemas."""
import pytest
from pydantic import ValidationError

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
    SerializedExample,
)
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


class TestRunCodemodSchemas:
    """Test the RunCodemod input and output schemas."""

    def test_run_codemod_input_valid(self):
        """Test that a valid RunCodemodInput can be created."""
        input_data = RunCodemodInput(
            input=RunCodemodInput.BaseRunCodemodInput(
                repo_full_name="test/repo",
                codemod_name="test_codemod",
                codemod_source="def test_codemod(): pass",
                codemod_run_type=CodemodRunType.DIFF,
                template_context={"key": "value"},
            )
        )
        assert input_data.input.repo_full_name == "test/repo"
        assert input_data.input.codemod_name == "test_codemod"
        assert input_data.input.codemod_source == "def test_codemod(): pass"
        assert input_data.input.codemod_run_type == CodemodRunType.DIFF
        assert input_data.input.template_context == {"key": "value"}

    def test_run_codemod_input_missing_required(self):
        """Test that RunCodemodInput raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            RunCodemodInput(
                input=RunCodemodInput.BaseRunCodemodInput(
                    # Missing repo_full_name
                    codemod_name="test_codemod",
                )
            )

    def test_run_codemod_output_valid(self):
        """Test that a valid RunCodemodOutput can be created."""
        output_data = RunCodemodOutput(
            success=True,
            web_link="https://example.com/run/123",
            logs="Codemod executed successfully",
            observation="Changes applied",
            error=None,
        )
        assert output_data.success is True
        assert output_data.web_link == "https://example.com/run/123"
        assert output_data.logs == "Codemod executed successfully"
        assert output_data.observation == "Changes applied"
        assert output_data.error is None

    def test_run_codemod_output_defaults(self):
        """Test that RunCodemodOutput uses correct defaults."""
        output_data = RunCodemodOutput()
        assert output_data.success is False
        assert output_data.web_link is None
        assert output_data.logs is None
        assert output_data.observation is None
        assert output_data.error is None


class TestAskExpertSchemas:
    """Test the AskExpert input and output schemas."""

    def test_ask_expert_input_valid(self):
        """Test that a valid AskExpertInput can be created."""
        input_data = AskExpertInput(
            input=AskExpertInput.BaseAskExpertInput(
                query="How do I create a codemod?",
            )
        )
        assert input_data.input.query == "How do I create a codemod?"

    def test_ask_expert_input_missing_required(self):
        """Test that AskExpertInput raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            AskExpertInput(
                input=AskExpertInput.BaseAskExpertInput(
                    # Missing query
                )
            )

    def test_ask_expert_response_valid(self):
        """Test that a valid AskExpertResponse can be created."""
        response_data = AskExpertResponse(
            response="This is the expert's answer",
            success=True,
        )
        assert response_data.response == "This is the expert's answer"
        assert response_data.success is True

    def test_ask_expert_response_missing_required(self):
        """Test that AskExpertResponse raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            AskExpertResponse(
                # Missing response
                success=True,
            )


class TestDocsSchemas:
    """Test the Docs input and output schemas."""

    def test_docs_input_valid(self):
        """Test that a valid DocsInput can be created."""
        input_data = DocsInput(
            docs_input=DocsInput.BaseDocsInput(
                repo_full_name="test/repo",
            )
        )
        assert input_data.docs_input.repo_full_name == "test/repo"

    def test_docs_input_missing_required(self):
        """Test that DocsInput raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            DocsInput(
                docs_input=DocsInput.BaseDocsInput(
                    # Missing repo_full_name
                )
            )

    def test_serialized_example_valid(self):
        """Test that a valid SerializedExample can be created."""
        example = SerializedExample(
            name="Example Name",
            description="Example Description",
            source="def example(): pass",
            language=ProgrammingLanguage.PYTHON,
            docstring="Example docstring",
        )
        assert example.name == "Example Name"
        assert example.description == "Example Description"
        assert example.source == "def example(): pass"
        assert example.language == ProgrammingLanguage.PYTHON
        assert example.docstring == "Example docstring"

    def test_serialized_example_minimal(self):
        """Test that a minimal SerializedExample can be created."""
        example = SerializedExample(
            source="def example(): pass",
            language=ProgrammingLanguage.PYTHON,
        )
        assert example.name is None
        assert example.description is None
        assert example.source == "def example(): pass"
        assert example.language == ProgrammingLanguage.PYTHON
        assert example.docstring == ""

    def test_docs_response_valid(self):
        """Test that a valid DocsResponse can be created."""
        response_data = DocsResponse(
            docs={"test_doc": "Test documentation"},
            examples=[
                SerializedExample(
                    name="Example Name",
                    source="def example(): pass",
                    language=ProgrammingLanguage.PYTHON,
                )
            ],
            language=ProgrammingLanguage.PYTHON,
        )
        assert response_data.docs == {"test_doc": "Test documentation"}
        assert len(response_data.examples) == 1
        assert response_data.examples[0].name == "Example Name"
        assert response_data.examples[0].source == "def example(): pass"
        assert response_data.language == ProgrammingLanguage.PYTHON


class TestCreateSchemas:
    """Test the Create input and output schemas."""

    def test_create_input_valid(self):
        """Test that a valid CreateInput can be created."""
        input_data = CreateInput(
            input=CreateInput.BaseCreateInput(
                name="test_codemod",
                query="Create a test codemod",
                language=ProgrammingLanguage.PYTHON,
            )
        )
        assert input_data.input.name == "test_codemod"
        assert input_data.input.query == "Create a test codemod"
        assert input_data.input.language == ProgrammingLanguage.PYTHON

    def test_create_input_missing_required(self):
        """Test that CreateInput raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            CreateInput(
                input=CreateInput.BaseCreateInput(
                    name="test_codemod",
                    # Missing query
                    language=ProgrammingLanguage.PYTHON,
                )
            )

    def test_create_response_valid(self):
        """Test that a valid CreateResponse can be created."""
        response_data = CreateResponse(
            codemod="def test_codemod(): pass",
            success=True,
        )
        assert response_data.codemod == "def test_codemod(): pass"
        assert response_data.success is True


class TestIdentifySchemas:
    """Test the Identify response schema."""

    def test_identify_response_valid(self):
        """Test that a valid IdentifyResponse can be created."""
        response_data = IdentifyResponse(
            codemod_name="test_codemod",
            success=True,
        )
        assert response_data.codemod_name == "test_codemod"
        assert response_data.success is True


class TestDeploySchemas:
    """Test the Deploy input and output schemas."""

    def test_deploy_input_valid(self):
        """Test that a valid DeployInput can be created."""
        input_data = DeployInput(
            input=DeployInput.BaseDeployInput(
                codemod_name="test_codemod",
                codemod_source="def test_codemod(): pass",
                repo_full_name="test/repo",
                lint_mode=True,
                lint_user_whitelist=["user1", "user2"],
                message="Test deployment",
                arguments_schema={"arg1": {"type": "string"}},
            )
        )
        assert input_data.input.codemod_name == "test_codemod"
        assert input_data.input.codemod_source == "def test_codemod(): pass"
        assert input_data.input.repo_full_name == "test/repo"
        assert input_data.input.lint_mode is True
        assert input_data.input.lint_user_whitelist == ["user1", "user2"]
        assert input_data.input.message == "Test deployment"
        assert input_data.input.arguments_schema == {"arg1": {"type": "string"}}

    def test_deploy_input_missing_required(self):
        """Test that DeployInput raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            DeployInput(
                input=DeployInput.BaseDeployInput(
                    # Missing codemod_name
                    codemod_source="def test_codemod(): pass",
                    repo_full_name="test/repo",
                )
            )

    def test_deploy_response_valid(self):
        """Test that a valid DeployResponse can be created."""
        response_data = DeployResponse(
            success=True,
            codemod_id=123,
        )
        assert response_data.success is True
        assert response_data.codemod_id == 123


class TestLookupSchemas:
    """Test the Lookup input and output schemas."""

    def test_lookup_input_valid(self):
        """Test that a valid LookupInput can be created."""
        input_data = LookupInput(
            input=LookupInput.BaseLookupInput(
                codemod_name="test_codemod",
                repo_full_name="test/repo",
            )
        )
        assert input_data.input.codemod_name == "test_codemod"
        assert input_data.input.repo_full_name == "test/repo"

    def test_lookup_input_missing_required(self):
        """Test that LookupInput raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            LookupInput(
                input=LookupInput.BaseLookupInput(
                    # Missing codemod_name
                    repo_full_name="test/repo",
                )
            )

    def test_lookup_output_valid(self):
        """Test that a valid LookupOutput can be created."""
        # Note: This test depends on the actual structure of LookupOutput.Codemod
        # Adjust as needed based on the actual schema
        response_data = LookupOutput(
            success=True,
            codemod=LookupOutput.Codemod(
                id=123,
                name="test_codemod",
                source="def test_codemod(): pass",
            ),
        )
        assert response_data.success is True
        assert response_data.codemod.id == 123
        assert response_data.codemod.name == "test_codemod"
        assert response_data.codemod.source == "def test_codemod(): pass"


class TestRunOnPRSchemas:
    """Test the RunOnPR input and output schemas."""

    def test_run_on_pr_input_valid(self):
        """Test that a valid RunOnPRInput can be created."""
        input_data = RunOnPRInput(
            input=RunOnPRInput.BaseRunOnPRInput(
                codemod_name="test_codemod",
                repo_full_name="test/repo",
                github_pr_number=123,
                language="python",
            )
        )
        assert input_data.input.codemod_name == "test_codemod"
        assert input_data.input.repo_full_name == "test/repo"
        assert input_data.input.github_pr_number == 123
        assert input_data.input.language == "python"

    def test_run_on_pr_input_missing_required(self):
        """Test that RunOnPRInput raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            RunOnPRInput(
                input=RunOnPRInput.BaseRunOnPRInput(
                    codemod_name="test_codemod",
                    # Missing repo_full_name
                    github_pr_number=123,
                )
            )

    def test_run_on_pr_response_valid(self):
        """Test that a valid RunOnPRResponse can be created."""
        response_data = RunOnPRResponse(
            success=True,
            pr_number=123,
            repo_full_name="test/repo",
        )
        assert response_data.success is True
        assert response_data.pr_number == 123
        assert response_data.repo_full_name == "test/repo"


class TestPRLookupSchemas:
    """Test the PRLookup input and output schemas."""

    def test_pr_lookup_input_valid(self):
        """Test that a valid PRLookupInput can be created."""
        input_data = PRLookupInput(
            input=PRLookupInput.BasePRLookupInput(
                repo_full_name="test/repo",
                github_pr_number=123,
            )
        )
        assert input_data.input.repo_full_name == "test/repo"
        assert input_data.input.github_pr_number == 123

    def test_pr_lookup_input_missing_required(self):
        """Test that PRLookupInput raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            PRLookupInput(
                input=PRLookupInput.BasePRLookupInput(
                    # Missing repo_full_name
                    github_pr_number=123,
                )
            )

    def test_pr_lookup_response_valid(self):
        """Test that a valid PRLookupResponse can be created."""
        response_data = PRLookupResponse(
            success=True,
            pr_number=123,
            repo_full_name="test/repo",
            status="completed",
        )
        assert response_data.success is True
        assert response_data.pr_number == 123
        assert response_data.repo_full_name == "test/repo"
        assert response_data.status == "completed"


class TestImproveCodemodSchemas:
    """Test the ImproveCodemod input and output schemas."""

    def test_improve_codemod_input_valid(self):
        """Test that a valid ImproveCodemodInput can be created."""
        input_data = ImproveCodemodInput(
            input=ImproveCodemodInput.BaseImproveCodemodInput(
                codemod="def test_codemod(): pass",
                task="Improve error handling",
                concerns=["error_handling", "performance"],
                context={"file_type": "python"},
                language=ProgrammingLanguage.PYTHON,
            )
        )
        assert input_data.input.codemod == "def test_codemod(): pass"
        assert input_data.input.task == "Improve error handling"
        assert input_data.input.concerns == ["error_handling", "performance"]
        assert input_data.input.context == {"file_type": "python"}
        assert input_data.input.language == ProgrammingLanguage.PYTHON

    def test_improve_codemod_input_missing_required(self):
        """Test that ImproveCodemodInput raises ValidationError when missing required fields."""
        with pytest.raises(ValidationError):
            ImproveCodemodInput(
                input=ImproveCodemodInput.BaseImproveCodemodInput(
                    # Missing codemod
                    task="Improve error handling",
                    concerns=["error_handling"],
                    context={},
                    language=ProgrammingLanguage.PYTHON,
                )
            )

    def test_improve_codemod_response_valid(self):
        """Test that a valid ImproveCodemodResponse can be created."""
        response_data = ImproveCodemodResponse(
            success=True,
            improved_codemod="def improved_codemod(): pass",
        )
        assert response_data.success is True
        assert response_data.improved_codemod == "def improved_codemod(): pass"

