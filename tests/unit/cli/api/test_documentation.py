import inspect

import pytest

from graph_sitter.cli.api.client import RestAPI


@pytest.fixture
def api_client():
    """Create a RestAPI client with a mock auth token."""
    return RestAPI(auth_token="mock_token")


class TestDocumentation:
    """Test documentation in the RestAPI client."""

    def test_class_docstring(self):
        """Test that the RestAPI class has a docstring."""
        assert RestAPI.__doc__ is not None
        assert len(RestAPI.__doc__) > 0

    def test_method_docstrings(self, api_client):
        """Test that all public methods have docstrings."""
        # Get all public methods
        methods = [
            name for name, func in inspect.getmembers(api_client, inspect.ismethod)
            if not name.startswith("_")
        ]
        
        # Verify that each method has a docstring
        for method_name in methods:
            method = getattr(api_client, method_name)
            assert method.__doc__ is not None, f"Method {method_name} is missing a docstring"
            assert len(method.__doc__) > 0, f"Method {method_name} has an empty docstring"

    def test_private_method_docstrings(self, api_client):
        """Test that all private methods have docstrings."""
        # Get all private methods (excluding dunder methods)
        methods = [
            name for name, func in inspect.getmembers(api_client, inspect.ismethod)
            if name.startswith("_") and not name.startswith("__")
        ]
        
        # Verify that each method has a docstring
        for method_name in methods:
            method = getattr(api_client, method_name)
            assert method.__doc__ is not None, f"Method {method_name} is missing a docstring"
            assert len(method.__doc__) > 0, f"Method {method_name} has an empty docstring"

    def test_run_docstring(self, api_client):
        """Test that the run method has a complete docstring."""
        docstring = api_client.run.__doc__
        assert docstring is not None
        assert "function" in docstring
        assert "include_source" in docstring
        assert "run_type" in docstring
        assert "template_context" in docstring

    def test_get_docs_docstring(self, api_client):
        """Test that the get_docs method has a complete docstring."""
        docstring = api_client.get_docs.__doc__
        assert docstring is not None
        assert "documentation" in docstring.lower()

    def test_ask_expert_docstring(self, api_client):
        """Test that the ask_expert method has a complete docstring."""
        docstring = api_client.ask_expert.__doc__
        assert docstring is not None
        assert "expert" in docstring.lower()
        assert "question" in docstring.lower()

    def test_create_docstring(self, api_client):
        """Test that the create method has a complete docstring."""
        docstring = api_client.create.__doc__
        assert docstring is not None
        assert "starter code" in docstring.lower()

    def test_identify_docstring(self, api_client):
        """Test that the identify method has a complete docstring."""
        docstring = api_client.identify.__doc__
        assert docstring is not None
        assert "identify" in docstring.lower()

    def test_deploy_docstring(self, api_client):
        """Test that the deploy method has a complete docstring."""
        docstring = api_client.deploy.__doc__
        assert docstring is not None
        assert "deploy" in docstring.lower()
        assert "codemod" in docstring.lower()

    def test_lookup_docstring(self, api_client):
        """Test that the lookup method has a complete docstring."""
        docstring = api_client.lookup.__doc__
        assert docstring is not None
        assert "look up" in docstring.lower()
        assert "codemod" in docstring.lower()

    def test_run_on_pr_docstring(self, api_client):
        """Test that the run_on_pr method has a complete docstring."""
        docstring = api_client.run_on_pr.__doc__
        assert docstring is not None
        assert "webhook" in docstring.lower()
        assert "pr" in docstring.lower()

    def test_lookup_pr_docstring(self, api_client):
        """Test that the lookup_pr method has a complete docstring."""
        docstring = api_client.lookup_pr.__doc__
        assert docstring is not None
        assert "look up" in docstring.lower()
        assert "pr" in docstring.lower()

    def test_improve_codemod_docstring(self, api_client):
        """Test that the improve_codemod method has a complete docstring."""
        docstring = api_client.improve_codemod.__doc__
        assert docstring is not None
        assert "improve" in docstring.lower()
        assert "codemod" in docstring.lower()

