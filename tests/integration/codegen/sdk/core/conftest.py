import pytest

from graph_sitter.code_generation.codegen_sdk_codebase import get_codegen_sdk_codebase


@pytest.fixture(scope="module")
def codebase():
    return get_codegen_sdk_codebase()
