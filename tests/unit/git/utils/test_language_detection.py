import pytest

from graph_sitter.codebase.factory.get_session import get_codebase_session
from graph_sitter.git.utils.language import determine_project_language
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage


@pytest.mark.parametrize(
    "strategy, expected_language",
    [
        ("package_json", ProgrammingLanguage.PYTHON),  # Check for package.json -> False, therefore return PYTHON
        ("git_most_common", ProgrammingLanguage.PYTHON),  # Check for git_most_common -> PYTHON
        ("most_common", ProgrammingLanguage.PYTHON),  # Check for most_common -> PYTHON
    ],
)
def test_determine_language_python(tmpdir, strategy, expected_language) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": "", "file2.py": "", "file3.py": ""}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        assert determine_project_language(tmpdir, strategy=strategy) == expected_language


@pytest.mark.parametrize(
    "strategy, expected_language",
    [
        ("package_json", ProgrammingLanguage.PYTHON),  # Check for package.json -> False, therefore return PYTHON (THIS IS EXPECTED, even if it's a TS project)
        ("git_most_common", ProgrammingLanguage.TYPESCRIPT),  # Check for git_most_common -> TYPESCRIPT
        ("most_common", ProgrammingLanguage.TYPESCRIPT),  # Check for most_common -> TYPESCRIPT
    ],
)
def test_determine_language_typescript(tmpdir, strategy, expected_language) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": "", "file2.ts": "", "file3.ts": ""}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        assert determine_project_language(tmpdir, strategy=strategy) == expected_language


@pytest.mark.parametrize(
    "strategy, expected_language",
    [
        ("package_json", ProgrammingLanguage.PYTHON),  # Check for package.json -> False, therefore return PYTHON (THIS IS EXPECTED)
        ("git_most_common", ProgrammingLanguage.OTHER),  # Check for git_most_common -> OTHER
        ("most_common", ProgrammingLanguage.OTHER),  # Check for most_common -> OTHER
    ],
)
def test_determine_language_other(tmpdir, strategy, expected_language) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"file1.txt": "", "file2.txt": "", "file3.txt": ""}, programming_language=ProgrammingLanguage.OTHER) as codebase:
        assert determine_project_language(tmpdir, strategy=strategy) == expected_language


@pytest.mark.parametrize(
    "strategy, expected_language",
    [
        ("package_json", ProgrammingLanguage.TYPESCRIPT),  # Check for package.json -> True, therefore return Typescript
        ("git_most_common", ProgrammingLanguage.OTHER),  # Check for git_most_common -> OTHER
        ("most_common", ProgrammingLanguage.OTHER),  # Check for most_common -> OTHER
    ],
)
def test_determine_language_package_json(tmpdir, strategy, expected_language) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"package.json": ""}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        assert determine_project_language(tmpdir, strategy=strategy) == expected_language


@pytest.mark.parametrize(
    "strategy, expected_language",
    [
        ("package_json", ProgrammingLanguage.PYTHON),  # Check for package.json -> False, therefore return PYTHON
        ("git_most_common", ProgrammingLanguage.PYTHON),  # Check for git_most_common -> PYTHON
        ("most_common", ProgrammingLanguage.PYTHON),  # Check for most_common -> PYTHON
    ],
)
def test_determine_language_mixed(tmpdir, strategy, expected_language) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "py_file1.py": "",
            "py_file2.py": "",  # 2 python files
            "ts_file1.ts": "",  # 1 typescript file
            "txt_file1.txt": "",  # 1 text file
        },
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        assert determine_project_language(tmpdir, strategy=strategy) == expected_language


@pytest.mark.parametrize(
    "strategy, expected_language",
    [
        ("package_json", ProgrammingLanguage.PYTHON),  # Check for package.json -> False, therefore return PYTHON
        ("git_most_common", ProgrammingLanguage.OTHER),  # Check for git_most_common -> OTHER
        ("most_common", ProgrammingLanguage.OTHER),  # Check for most_common -> OTHER
    ],
)
def test_determine_language_threshold(tmpdir, strategy, expected_language) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"file0.py": ""} | {f"file{i}.txt": "" for i in range(1, 20)}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        assert determine_project_language(tmpdir, strategy=strategy) == expected_language


@pytest.mark.parametrize(
    "strategy, expected_language",
    [
        ("package_json", ProgrammingLanguage.PYTHON),  # Check for package.json -> False, therefore return PYTHON
        ("git_most_common", ProgrammingLanguage.OTHER),  # Check for git_most_common -> OTHER (follows gitignore, therefore finds no files)
        ("most_common", ProgrammingLanguage.PYTHON),  # Check for most_common -> PYTHON (ignores gitignore)
    ],
)
def test_determine_language_gitignore(tmpdir, strategy, expected_language) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": "", "dir/file2.py": "", "dir/file3.py": "", ".gitignore": "dir"}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        assert determine_project_language(tmpdir, strategy=strategy) == expected_language
