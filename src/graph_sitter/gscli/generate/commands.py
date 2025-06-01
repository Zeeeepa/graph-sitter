import json
import os
import re
import shutil
from pathlib import Path
from typing import Optional

import click
from termcolor import colored

import graph_sitter as sdk
from graph_sitter.ai.client import get_openai_client
from graph_sitter.code_generation.changelog_generation import generate_changelog
from graph_sitter.code_generation.codegen_sdk_codebase import get_codegen_sdk_codebase
from graph_sitter.code_generation.doc_utils.generate_docs_json import generate_docs_json
from graph_sitter.code_generation.mdx_docs_generation import render_mdx_page_for_class
from graph_sitter.gscli.generate.runner_imports import _generate_runner_imports
from graph_sitter.gscli.generate.system_prompt import get_system_prompt
from graph_sitter.gscli.generate.utils import LanguageType, generate_builtins_file
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

AUTO_GENERATED_COMMENT = "THE CODE BELOW IS AUTO GENERATED. UPDATE THE SNIPPET BY UPDATING THE SKILL"
CODE_SNIPPETS_REGEX = r"(?:```python\n(?:(?!```)[\\s\\S])*?\n```|<CodeGroup>(?:(?!</CodeGroup>)[\\s\\S])*?</CodeGroup>)"


def validate_directory_path(path: str, create_if_missing: bool = False) -> Path:
    """Validate and normalize directory path with optional creation."""
    try:
        path_obj = Path(path).resolve()
        if create_if_missing:
            path_obj.mkdir(parents=True, exist_ok=True)
        elif not path_obj.exists():
            raise click.ClickException(f"Directory does not exist: {path}")
        elif not path_obj.is_dir():
            raise click.ClickException(f"Path is not a directory: {path}")
        return path_obj
    except (OSError, PermissionError) as e:
        raise click.ClickException(f"Invalid directory path '{path}': {e}")


def validate_file_path(path: str, must_exist: bool = True) -> Path:
    """Validate and normalize file path."""
    try:
        path_obj = Path(path).resolve()
        if must_exist and not path_obj.exists():
            raise click.ClickException(f"File does not exist: {path}")
        return path_obj
    except (OSError, PermissionError) as e:
        raise click.ClickException(f"Invalid file path '{path}': {e}")


@click.group()
def generate() -> None:
    """Commands for running auto-generate commands, currently for typestubs, imports to include in runners, and docs"""
    ...


@generate.command()
@click.argument("docs_dir", default="docs", required=False)
def docs(docs_dir: str) -> None:
    """Compile new .MDX files for the auto-generated docs pages and write them to the file system.
    To actually deploy these changes, you must commit and merge the changes into develop

    This will generate docs using the codebase locally, including any unstaged changes
    """
    try:
        docs_path = validate_directory_path(docs_dir, create_if_missing=True)
        generate_docs(str(docs_path))
        click.echo(colored(f"✓ Successfully generated docs in {docs_path}", "green"))
    except Exception as e:
        logger.error(f"Failed to generate docs: {e}")
        raise click.ClickException(f"Documentation generation failed: {e}")


@generate.command()
@click.argument("imports_file", default="function_imports.py", required=False)
def runner_imports(imports_file: str) -> None:
    """Generate imports to include in runner execution environment"""
    try:
        imports_path = validate_file_path(imports_file, must_exist=False)
        _generate_runner_imports(str(imports_path))
        click.echo(colored(f"✓ Successfully generated runner imports in {imports_path}", "green"))
    except Exception as e:
        logger.error(f"Failed to generate runner imports: {e}")
        raise click.ClickException(f"Runner imports generation failed: {e}")


@generate.command()
@click.option("--output-dir", default="typings", help="Output directory for generated typestubs")
@click.option("--frontend-dir", default=None, help="Frontend typestubs directory (optional)")
def typestubs(output_dir: str, frontend_dir: Optional[str]) -> None:
    """Generate typestubs for the the graphsitter Codebase module
    The Codebase class and it's constituents contain methods that should not be exposed, i.e we have private methods
    and private properties that we'd like to keep internal. So the way this works is we generate the typestubs and the remove
    the "internal" symbols. For example we'll remove:
     - "_" prefixed methods and properties
     - methods with `@noapidocs` decorator
    """
    try:
        _generate_codebase_typestubs(output_dir, frontend_dir)
        click.echo(colored("✓ Successfully generated typestubs", "green"))
    except Exception as e:
        logger.error(f"Failed to generate typestubs: {e}")
        raise click.ClickException(f"Typestub generation failed: {e}")


def _generate_codebase_typestubs(output_dir: str = "typings", frontend_dir: Optional[str] = None) -> None:
    """Generate typestubs with configurable output directories."""
    initial_dir = Path.cwd()
    
    # Validate we're in a reasonable location (look for pyproject.toml or setup.py)
    if not any((initial_dir / f).exists() for f in ["pyproject.toml", "setup.py", "setup.cfg"]):
        click.echo(colored("Warning: No Python project files found in current directory", "yellow"))
    
    out_dir = initial_dir / output_dir
    
    # Determine frontend directory
    if frontend_dir is None:
        # Try to find a reasonable default
        possible_frontend_dirs = [
            initial_dir.parent / "codegen-frontend/assets/typestubs/graphsitter",
            initial_dir / "frontend/assets/typestubs/graphsitter",
            initial_dir / "typestubs/graphsitter"
        ]
        frontend_typestubs_dir = next((d for d in possible_frontend_dirs if d.parent.exists()), out_dir / "graphsitter")
    else:
        frontend_typestubs_dir = Path(frontend_dir)
    
    # Clean existing directories
    for dir_path in [out_dir, frontend_typestubs_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Generate typestubs using pyright
    typestub_commands = [
        "uv run pyright -p . --createstub graph_sitter.core.codebase",
        "uv run pyright -p . --createstub graph_sitter.git",
        "uv run pyright -p . --createstub networkx",
        "uv run pyright -p . --createstub app.codemod.compilation.models.context",
        "uv run pyright -p . --createstub app.codemod.compilation.models.pr_options",
        "uv run pyright -p . --createstub app.codemod.compilation.models.github_named_user_context",
        "uv run pyright -p . --createstub app.codemod.compilation.models.pull_request_context",
        "uv run pyright -p . --createstub app.codemod.compilation.models.pr_part_context",
    ]
    
    for cmd in typestub_commands:
        result = os.system(cmd)
        if result != 0:
            logger.warning(f"Command failed with exit code {result}: {cmd}")
    
    # Generate builtins files
    try:
        generate_builtins_file(str(frontend_typestubs_dir / "__builtins__.pyi"), LanguageType.BOTH)
        generate_builtins_file(str(frontend_typestubs_dir / "__builtins__python__.pyi"), LanguageType.PYTHON)
        generate_builtins_file(str(frontend_typestubs_dir / "__builtins__typescript__.pyi"), LanguageType.TYPESCRIPT)
    except Exception as e:
        logger.error(f"Failed to generate builtins files: {e}")
        raise
    
    # Clean up temporary output directory if it exists
    if out_dir.exists() and out_dir != frontend_typestubs_dir:
        shutil.rmtree(out_dir)


def generate_docs(docs_dir: str) -> None:
    """Compile new .MDX files for the auto-generated docs pages and write them to the file system.
    To actually deploy these changes, you must commit and merge the changes into develop

    This will generate docs using the codebase locally, including any unstaged changes
    """
    try:
        generate_codegen_sdk_docs(docs_dir)
    except Exception as e:
        logger.error(f"Failed to generate docs: {e}")
        raise


@generate.command()
@click.argument("filepath", default=sdk.__path__[0] + "/system-prompt.txt", required=False)
def system_prompt(filepath: str) -> None:
    """Generate system prompt and write to specified file."""
    try:
        output_path = validate_file_path(filepath, must_exist=False)
        print(f"Generating system prompt and writing to {output_path}...")
        
        new_system_prompt = get_system_prompt()
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_system_prompt)
            
        print(colored(f"✓ Successfully wrote system prompt to {output_path}", "green"))
    except Exception as e:
        logger.error(f"Failed to generate system prompt: {e}")
        raise click.ClickException(f"System prompt generation failed: {e}")


def get_snippet_pattern(target_name: str) -> str:
    pattern = rf"\\[//\\]: # \\(--{re.escape(target_name)}--\\)\\s*(?:\\[//\\]: # \\(--{re.escape(AUTO_GENERATED_COMMENT)}--\\)\\s*)?"
    pattern += CODE_SNIPPETS_REGEX
    return pattern


def generate_codegen_sdk_docs(docs_dir: str) -> None:
    """Generate the docs for the codegen_sdk API and update the mint.json"""
    print(colored("Generating codegen_sdk docs", "green"))

    try:
        # Generate docs page for codebase api and write to the file system
        codebase = get_codegen_sdk_codebase()
        gs_docs = generate_docs_json(codebase, "HEAD")

        docs_path = Path(docs_dir)
        
        # Prepare the directories for the new docs
        # Delete existing documentation directories if they exist
        # So we remove generated docs for any classes which no longer exist
        python_docs_dir = docs_path / "api-reference" / "python"
        typescript_docs_dir = docs_path / "api-reference" / "typescript"
        core_dir = docs_path / "api-reference" / "core"

        for dir_path in [python_docs_dir, typescript_docs_dir, core_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)

        # Generate the docs pages for core, python, and typescript classes
        # Write the generated docs to the file system, splitting between core, python, and typescript
        # keep track of where we put each one so we can update the mint.json
        python_set = set()
        typescript_set = set()
        core_set = set()
        
        for class_doc in gs_docs.classes:
            class_name = class_doc.title
            lower_class_name = class_name.lower()
            
            if lower_class_name.startswith("py"):
                file_path = python_docs_dir / f"{class_name}.mdx"
                python_set.add(f"api-reference/python/{class_name}")
            elif lower_class_name.startswith(("ts", "jsx")):
                file_path = typescript_docs_dir / f"{class_name}.mdx"
                typescript_set.add(f"api-reference/typescript/{class_name}")
            else:
                file_path = core_dir / f"{class_name}.mdx"
                core_set.add(f"api-reference/core/{class_name}")

            mdx_page = render_mdx_page_for_class(cls_doc=class_doc)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(mdx_page)
                
        print(colored("Finished writing new .mdx files", "green"))

        # Update the core, python, and typescript page sets in mint.json
        mint_file_path = docs_path / "mint.json"
        
        if not mint_file_path.exists():
            logger.warning(f"mint.json not found at {mint_file_path}")
            return
            
        with open(mint_file_path, encoding="utf-8") as mint_file:
            mint_data = json.load(mint_file)

        # Find the "API Reference" group where we want to add the pages
        api_ref_group = next((group for group in mint_data["navigation"] if group["group"] == "API Reference"), None)
        
        if not api_ref_group:
            logger.warning("API Reference group not found in mint.json")
            return

        # Update the pages for each language group
        for group in api_ref_group["pages"]:
            if isinstance(group, dict):  # Ensure group is a dictionary
                if group["group"] == "Core":
                    group["pages"] = sorted(core_set)
                elif group["group"] == "Python":
                    group["pages"] = sorted(python_set)
                elif group["group"] == "Typescript":
                    group["pages"] = sorted(typescript_set)

        with open(mint_file_path, "w", encoding="utf-8") as mint_file:
            json.dump(mint_data, mint_file, indent=2)

        print(colored("Updated mint.json with new page sets", "green"))
        
    except Exception as e:
        logger.error(f"Failed to generate codegen SDK docs: {e}")
        raise


@generate.command()
@click.option("--docs-dir", default="docs", required=False, help="Documentation directory")
@click.option("--openai-key", required=True, help="OpenAI API key for changelog generation")
@click.option("--complete", is_flag=True, help="Generate a complete changelog for the codegen_sdk API")
def changelog(docs_dir: str, openai_key: str, complete: bool = False) -> None:
    """Generate the changelog for the codegen_sdk API and update the changelog.mdx file"""
    try:
        docs_path = validate_directory_path(docs_dir)
        changelog_file = docs_path / "changelog" / "changelog.mdx"
        
        # Ensure changelog directory exists
        changelog_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(colored("Generating changelog", "green"))
        header = """---
title: "Graph-sitter Updates"
icon: "clock"
iconType: "solid"
---
"""

        client = get_openai_client(openai_key)

        if complete:
            entire_release_history = generate_changelog(client)
            new_changelog = header + entire_release_history
        else:
            # Read existing changelog and append new releases
            if changelog_file.exists():
                with open(changelog_file, encoding="utf-8") as f:
                    existing_changelog = f.read()
                    
                # Remove header from existing changelog
                if header in existing_changelog:
                    existing_changelog = existing_changelog.split(header)[1]
                    
                # Find the latest existing version
                latest_existing_version = re.search(r'label="(v[\\d.]+)"', existing_changelog)
                
                if latest_existing_version:
                    # Generate new releases
                    new_releases = generate_changelog(client, latest_existing_version.group(1))
                    new_changelog = header + new_releases + existing_changelog
                else:
                    # If there is no latest existing version, generate a complete changelog
                    new_releases = generate_changelog(client)
                    new_changelog = header + new_releases
            else:
                # Generate complete changelog if file doesn't exist
                new_releases = generate_changelog(client)
                new_changelog = header + new_releases

        with open(changelog_file, "w", encoding="utf-8") as f:
            f.write(new_changelog)
            
        print(colored(f"✓ Successfully generated changelog at {changelog_file}", "green"))
        
    except Exception as e:
        logger.error(f"Failed to generate changelog: {e}")
        raise click.ClickException(f"Changelog generation failed: {e}")
