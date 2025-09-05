import pytest

from graph_sitter.cli.api.schemas import CodemodRunType


class TestEnums:
    """Test enum classes used by the API client."""

    def test_codemod_run_type_values(self):
        """Test the CodemodRunType enum values."""
        # Verify the enum values
        assert CodemodRunType.DIFF == "diff"
        assert CodemodRunType.PR == "pr"

    def test_codemod_run_type_members(self):
        """Test the CodemodRunType enum members."""
        # Verify the enum members
        assert list(CodemodRunType) == [CodemodRunType.DIFF, CodemodRunType.PR]

    def test_codemod_run_type_names(self):
        """Test the CodemodRunType enum names."""
        # Verify the enum names
        assert CodemodRunType.DIFF.name == "DIFF"
        assert CodemodRunType.PR.name == "PR"

    def test_codemod_run_type_comparison(self):
        """Test comparing CodemodRunType enum values."""
        # Verify enum value comparison
        assert CodemodRunType.DIFF == CodemodRunType.DIFF
        assert CodemodRunType.PR == CodemodRunType.PR
        assert CodemodRunType.DIFF != CodemodRunType.PR

    def test_codemod_run_type_string_comparison(self):
        """Test comparing CodemodRunType enum values with strings."""
        # Verify enum value comparison with strings
        assert CodemodRunType.DIFF == "diff"
        assert CodemodRunType.PR == "pr"
        assert CodemodRunType.DIFF != "pr"
        assert CodemodRunType.PR != "diff"

    def test_codemod_run_type_from_string(self):
        """Test creating CodemodRunType enum values from strings."""
        # Verify creating enum values from strings
        assert CodemodRunType("diff") == CodemodRunType.DIFF
        assert CodemodRunType("pr") == CodemodRunType.PR

    def test_codemod_run_type_invalid_value(self):
        """Test creating CodemodRunType enum values with invalid strings."""
        # Verify that creating enum values with invalid strings raises an error
        with pytest.raises(ValueError):
            CodemodRunType("invalid")

