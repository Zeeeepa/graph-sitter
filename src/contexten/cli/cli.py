import rich_click as click
from rich.traceback import install

# Import contexten-specific commands
from contexten.cli.commands.agent.main import agent_command

# Import available graph_sitter commands
try:
    from graph_sitter.cli.commands.config.main import config_command
except ImportError:
    config_command = None

try:
    from graph_sitter.cli.commands.init.main import init_command
except ImportError:
    init_command = None

try:
    from graph_sitter.cli.commands.list.main import list_command
except ImportError:
    list_command = None

try:
    from graph_sitter.cli.commands.lsp.lsp import lsp_command
except ImportError:
    lsp_command = None

try:
    from graph_sitter.cli.commands.notebook.main import notebook_command
except ImportError:
    notebook_command = None

try:
    from graph_sitter.cli.commands.reset.main import reset_command
except ImportError:
    reset_command = None

try:
    from graph_sitter.cli.commands.run.main import run_command
except ImportError:
    run_command = None

try:
    from graph_sitter.cli.commands.start.main import start_command
except ImportError:
    start_command = None

try:
    from graph_sitter.cli.commands.style_debug.main import style_debug_command
except ImportError:
    style_debug_command = None

try:
    from graph_sitter.cli.commands.update.main import update_command
except ImportError:
    update_command = None

click.rich_click.USE_RICH_MARKUP = True
install(show_locals=True)


@click.group()
@click.version_option(prog_name="contexten", package_name="graph-sitter", message="%(version)s")
def main():
    """Contexten CLI - AI agent orchestrator."""


# Add available commands
main.add_command(agent_command)

if init_command:
    main.add_command(init_command)
if run_command:
    main.add_command(run_command)
if list_command:
    main.add_command(list_command)
if style_debug_command:
    main.add_command(style_debug_command)
if notebook_command:
    main.add_command(notebook_command)
if reset_command:
    main.add_command(reset_command)
if update_command:
    main.add_command(update_command)
if config_command:
    main.add_command(config_command)
if lsp_command:
    main.add_command(lsp_command)
if start_command:
    main.add_command(start_command)


if __name__ == "__main__":
    main()
