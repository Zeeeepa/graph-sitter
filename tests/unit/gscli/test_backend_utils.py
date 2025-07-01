import pytest

from graph_sitter.gscli.backend.utils import filepath_to_modulename


class TestFilepathToModulename:
    """Test the filepath_to_modulename utility function."""

    def test_basic_conversion(self):
        """Test basic filepath to module conversion."""
        assert filepath_to_modulename("src/mymodule/file.py") == "src.mymodule.file"
        assert filepath_to_modulename("src/mymodule/file") == "src.mymodule.file"

    def test_no_extension(self):
        """Test conversion without .py extension."""
        assert filepath_to_modulename("src/mymodule/file") == "src.mymodule.file"

    def test_single_file(self):
        """Test single file conversion."""
        assert filepath_to_modulename("file.py") == "file"
        assert filepath_to_modulename("file") == "file"

    def test_nested_paths(self):
        """Test deeply nested paths."""
        assert filepath_to_modulename("a/b/c/d/e.py") == "a.b.c.d.e"

    def test_whitespace_handling(self):
        """Test that whitespace is stripped."""
        assert filepath_to_modulename("  src/mymodule/file.py  ") == "src.mymodule.file"

    def test_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Filepath must be a non-empty string"):
            filepath_to_modulename("")

    def test_none_input(self):
        """Test that None input raises ValueError."""
        with pytest.raises(ValueError, match="Filepath must be a non-empty string"):
            filepath_to_modulename(None)

    def test_non_string_input(self):
        """Test that non-string input raises ValueError."""
        with pytest.raises(ValueError, match="Filepath must be a non-empty string"):
            filepath_to_modulename(123)

    def test_dangerous_characters(self):
        """Test that dangerous characters are rejected."""
        dangerous_paths = [
            "../malicious/file.py",
            "~/secret/file.py", 
            "$HOME/file.py",
            "src/../../../etc/passwd"
        ]
        
        for path in dangerous_paths:
            with pytest.raises(ValueError, match="potentially dangerous characters"):
                filepath_to_modulename(path)

    def test_path_normalization(self):
        """Test that paths are properly normalized."""
        # These should work (no dangerous traversal)
        assert filepath_to_modulename("src/./mymodule/file.py") == "src.mymodule.file"
        assert filepath_to_modulename("src//mymodule//file.py") == "src.mymodule.file"

    def test_windows_paths(self):
        """Test Windows-style paths are converted properly."""
        # Note: This test assumes the function handles backslashes
        # The current implementation uses Path.as_posix() which should normalize
        result = filepath_to_modulename("src\\mymodule\\file.py")
        assert result == "src.mymodule.file"

