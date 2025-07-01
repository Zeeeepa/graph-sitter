import pytest
from click.testing import CliRunner

from graph_sitter.gscli.cli import main as gscli_main


def test_cli():
    """Test that the gscli module can be imported without errors."""
    import graph_sitter.gscli  # noqa: F401


def test_gscli_main_help():
    """Test that the gscli main command shows help."""
    runner = CliRunner()
    result = runner.invoke(gscli_main, ['--help'])
    assert result.exit_code == 0
    assert 'Commands for running auto-generate commands' in result.output


def test_generate_commands_help():
    """Test that generate subcommands are available."""
    runner = CliRunner()
    result = runner.invoke(gscli_main, ['--help'])
    assert result.exit_code == 0
    
    # Check that main commands are listed
    expected_commands = ['docs', 'runner-imports', 'typestubs', 'system-prompt', 'changelog']
    for cmd in expected_commands:
        assert cmd in result.output


def test_docs_command_help():
    """Test docs command help."""
    runner = CliRunner()
    result = runner.invoke(gscli_main, ['docs', '--help'])
    assert result.exit_code == 0
    assert 'Compile new .MDX files' in result.output


def test_runner_imports_command_help():
    """Test runner-imports command help."""
    runner = CliRunner()
    result = runner.invoke(gscli_main, ['runner-imports', '--help'])
    assert result.exit_code == 0
    assert 'Generate imports to include in runner execution environment' in result.output


def test_typestubs_command_help():
    """Test typestubs command help."""
    runner = CliRunner()
    result = runner.invoke(gscli_main, ['typestubs', '--help'])
    assert result.exit_code == 0
    assert 'Generate typestubs' in result.output


def test_system_prompt_command_help():
    """Test system-prompt command help."""
    runner = CliRunner()
    result = runner.invoke(gscli_main, ['system-prompt', '--help'])
    assert result.exit_code == 0
    assert 'Generate system prompt' in result.output


def test_changelog_command_help():
    """Test changelog command help."""
    runner = CliRunner()
    result = runner.invoke(gscli_main, ['changelog', '--help'])
    assert result.exit_code == 0
    assert 'Generate the changelog' in result.output
