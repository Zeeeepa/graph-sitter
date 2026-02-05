"""
Graph-Sitter Tools Adapter - Consolidated Tool Collection
======================================================================

This module consolidates 8 specialized tool files:
- reveal_symbol_fn.py, reveal_symbol.py
- mdx_docs_generation.py, document_functions.py, generate_docs_json.py
- current_code_codebase.py, codegen_sdk_codebase.py, list_directory.py
"""


# ====================================================================
# SYMBOL ANALYSIS TOOLS - reveal_symbol_fn
# ====================================================================
# Source: reveal_symbol_fn.py

from logging import getLogger
from typing import Annotated

from graph_sitter.extensions.tools.reveal_symbol import reveal_symbol

logger = getLogger(__name__)


class RevealSymbolInput(BaseModel):
    """Input for revealing symbol relationships."""

    symbol_name: str = Field(..., description="Name of the symbol to analyze")
    degree: int = Field(
        default=1, description="How many degrees of separation to traverse"
    )
    max_tokens: int | None = Field(
        default=None,
        description="Optional maximum number of tokens for all source code combined",
    )
    collect_dependencies: bool = Field(
        default=True, description="Whether to collect dependencies"
    )
    collect_usages: bool = Field(default=True, description="Whether to collect usages")


class RevealSymbolTool(BaseTool):
    """Tool for revealing symbol relationships."""

    name: ClassVar[str] = "reveal_symbol"
    description: ClassVar[str] = (
        "Reveal the dependencies and usages of a symbol up to N degrees"
    )
    args_schema: ClassVar[type[BaseModel]] = RevealSymbolInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        symbol_name: str,
        degree: int = 1,
        max_tokens: int | None = None,
        collect_dependencies: bool = True,
        collect_usages: bool = True,
    ) -> str:
        result = reveal_symbol(
            codebase=self.codebase,
            symbol_name=symbol_name,
            max_depth=degree,
            max_tokens=max_tokens,
            collect_dependencies=collect_dependencies,
            collect_usages=collect_usages,
        )
        return result.render()


@mcp.tool(
    name="reveal_symbol",
    description="Shows all usages + dependencies of the provided symbol, up to the specified max depth (e.g. show 2nd-level usages/dependencies)",
)
async def reveal_symbol_fn(
    symbol: Annotated[str, "symbol to show usages and dependencies for"],
    filepath: Annotated[str, "file path to the target file to split"] = None,
    max_depth: Annotated[int, "maximum depth to show dependencies"] = 1,
):
    codebase = state.parsed_codebase
    output = reveal_symbol(
        codebase=codebase,
        symbol_name=symbol,
        filepath=filepath,
        max_depth=max_depth,
        max_tokens=10000,
    )
    return output



# ====================================================================
# SYMBOL ANALYSIS TOOLS - reveal_symbol
# ====================================================================
# Source: reveal_symbol.py

"""Tool for revealing symbol dependencies and usages."""

from typing import Any, ClassVar, Optional

import tiktoken
from pydantic import Field

from graph_sitter.sdk.ai.utils import count_tokens
from graph_sitter.sdk.core.codebase import Codebase
from graph_sitter.sdk.core.external_module import ExternalModule
from graph_sitter.sdk.core.import_resolution import Import
from graph_sitter.sdk.core.symbol import Symbol

from graph_sitter.extensions.tools.observation import Observation


class SymbolInfo(Observation):
    """Information about a symbol."""

    name: str = Field(description="Name of the symbol")
    filepath: Optional[str] = Field(description="Path to the file containing the symbol")
    source: str = Field(description="Source code of the symbol")

    str_template: ClassVar[str] = "{name} in {filepath}"


class RevealSymbolObservation(Observation):
    """Response from revealing symbol dependencies and usages."""

    dependencies: Optional[list[SymbolInfo]] = Field(
        default=None,
        description="List of symbols this symbol depends on",
    )
    usages: Optional[list[SymbolInfo]] = Field(
        default=None,
        description="List of symbols that use this symbol",
    )
    truncated: bool = Field(
        default=False,
        description="Whether results were truncated due to token limit",
    )
    valid_filepaths: Optional[list[str]] = Field(
        default=None,
        description="List of valid filepaths when symbol is ambiguous",
    )

    str_template: ClassVar[str] = "Symbol info: {dependencies_count} dependencies, {usages_count} usages"

    def _get_details(self) -> dict[str, Any]:
        """Get details for string representation."""
        return {
            "dependencies_count": len(self.dependencies or []),
            "usages_count": len(self.usages or []),
        }


def truncate_source(source: str, max_tokens: int) -> str:
    """Truncate source code to fit within max_tokens while preserving meaning.

    Attempts to keep the most important parts of the code by:
    1. Keeping function/class signatures
    2. Preserving imports
    3. Keeping the first and last parts of the implementation
    """
    if not max_tokens or max_tokens <= 0:
        return source

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(source)

    if len(tokens) <= max_tokens:
        return source

    # Split into lines while preserving line endings
    lines = source.splitlines(keepends=True)

    # Always keep first 2 lines (usually imports/signature) and last line (usually closing brace)
    if len(lines) <= 3:
        return source

    result = []
    current_tokens = 0

    # Keep first 2 lines
    for i in range(2):
        line = lines[i]
        line_tokens = len(enc.encode(line))
        if current_tokens + line_tokens > max_tokens:
            break
        result.append(line)
        current_tokens += line_tokens

    # Add truncation indicator
    truncation_msg = "    # ... truncated ...\n"
    truncation_tokens = len(enc.encode(truncation_msg))

    # Keep last line if we have room
    last_line = lines[-1]
    last_line_tokens = len(enc.encode(last_line))

    remaining_tokens = max_tokens - current_tokens - truncation_tokens - last_line_tokens

    if remaining_tokens > 0:
        # Try to keep some middle content
        for line in lines[2:-1]:
            line_tokens = len(enc.encode(line))
            if current_tokens + line_tokens > remaining_tokens:
                break
            result.append(line)
            current_tokens += line_tokens

    result.append(truncation_msg)
    result.append(last_line)

    return "".join(result)


def get_symbol_info(symbol: Symbol, max_tokens: Optional[int] = None) -> SymbolInfo:
    """Get relevant information about a symbol.

    Args:
        symbol: The symbol to get info for
        max_tokens: Optional maximum number of tokens for the source code

    Returns:
        Dict containing symbol metadata and source
    """
    source = symbol.source
    if max_tokens:
        source = truncate_source(source, max_tokens)

    return SymbolInfo(
        status="success",
        name=symbol.name,
        filepath=symbol.file.filepath if symbol.file else None,
        source=source,
    )


def hop_through_imports(symbol: Symbol, seen_imports: Optional[set[str]] = None) -> Symbol:
    """Follow import chain to find the root symbol, stopping at ExternalModule."""
    if seen_imports is None:
        seen_imports = set()

    # Base case: not an import or already seen
    if not isinstance(symbol, Import) or symbol in seen_imports:
        return symbol

    seen_imports.add(symbol.source)

    # Try to resolve the import
    if isinstance(symbol.imported_symbol, ExternalModule):
        return symbol.imported_symbol
    elif isinstance(symbol.imported_symbol, Import):
        return hop_through_imports(symbol.imported_symbol, seen_imports)
    elif isinstance(symbol.imported_symbol, Symbol):
        return symbol.imported_symbol
    else:
        return symbol.imported_symbol


def get_extended_context(
    symbol: Symbol,
    degree: int,
    max_tokens: Optional[int] = None,
    seen_symbols: Optional[set[Symbol]] = None,
    current_degree: int = 0,
    total_tokens: int = 0,
    collect_dependencies: bool = True,
    collect_usages: bool = True,
) -> tuple[list[SymbolInfo], list[SymbolInfo], int]:
    """Recursively collect dependencies and usages up to specified degree.

    Args:
        symbol: The symbol to analyze
        degree: How many degrees of separation to traverse
        max_tokens: Optional maximum number of tokens for all source code combined
        seen_symbols: Set of symbols already processed
        current_degree: Current recursion depth
        total_tokens: Running count of tokens collected
        collect_dependencies: Whether to collect dependencies
        collect_usages: Whether to collect usages

    Returns:
        Tuple of (dependencies, usages, total_tokens)
    """
    if seen_symbols is None:
        seen_symbols = set()

    if current_degree >= degree or symbol in seen_symbols:
        return [], [], total_tokens

    seen_symbols.add(symbol)

    # Get direct dependencies and usages
    dependencies = []
    usages = []

    # Helper to check if we're under token limit
    def under_token_limit() -> bool:
        return not max_tokens or total_tokens < max_tokens

    # Process dependencies
    if collect_dependencies:
        for dep in symbol.dependencies:
            if not under_token_limit():
                break

            dep = hop_through_imports(dep)
            if dep not in seen_symbols:
                # Calculate tokens for this symbol
                info = get_symbol_info(dep, max_tokens=max_tokens)
                symbol_tokens = count_tokens(info.source) if info.source else 0

                if max_tokens and total_tokens + symbol_tokens > max_tokens:
                    continue

                dependencies.append(info)
                total_tokens += symbol_tokens

                if current_degree + 1 < degree:
                    next_deps, next_uses, new_total = get_extended_context(dep, degree, max_tokens, seen_symbols, current_degree + 1, total_tokens, collect_dependencies, collect_usages)
                    dependencies.extend(next_deps)
                    usages.extend(next_uses)
                    total_tokens = new_total

    # Process usages
    if collect_usages:
        for usage in symbol.usages:
            if not under_token_limit():
                break

            usage = usage.usage_symbol
            usage = hop_through_imports(usage)
            if usage not in seen_symbols:
                # Calculate tokens for this symbol
                info = get_symbol_info(usage, max_tokens=max_tokens)
                symbol_tokens = count_tokens(info.source) if info.source else 0

                if max_tokens and total_tokens + symbol_tokens > max_tokens:
                    continue

                usages.append(info)
                total_tokens += symbol_tokens

                if current_degree + 1 < degree:
                    next_deps, next_uses, new_total = get_extended_context(usage, degree, max_tokens, seen_symbols, current_degree + 1, total_tokens, collect_dependencies, collect_usages)
                    dependencies.extend(next_deps)
                    usages.extend(next_uses)
                    total_tokens = new_total

    return dependencies, usages, total_tokens


def reveal_symbol(
    codebase: Codebase,
    symbol_name: str,
    filepath: Optional[str] = None,
    max_depth: Optional[int] = 1,
    max_tokens: Optional[int] = None,
    collect_dependencies: Optional[bool] = True,
    collect_usages: Optional[bool] = True,
) -> RevealSymbolObservation:
    """Reveal the dependencies and usages of a symbol up to N degrees.

    Args:
        codebase: The codebase to analyze
        symbol_name: The name of the symbol to analyze
        filepath: Optional filepath to the symbol to analyze
        max_depth: How many degrees of separation to traverse (default: 1)
        max_tokens: Optional maximum number of tokens for all source code combined
        collect_dependencies: Whether to collect dependencies (default: True)
        collect_usages: Whether to collect usages (default: True)

    Returns:
        Dict containing:
            - dependencies: List of symbols this symbol depends on (if collect_dependencies=True)
            - usages: List of symbols that use this symbol (if collect_usages=True)
            - truncated: Whether the results were truncated due to max_tokens
            - error: Optional error message if the symbol was not found
    """
    symbols = codebase.get_symbols(symbol_name=symbol_name)
    if len(symbols) == 0:
        return RevealSymbolObservation(
            status="error",
            error=f"{symbol_name} not found",
        )
    if len(symbols) > 1:
        return RevealSymbolObservation(
            status="error",
            error=f"{symbol_name} is ambiguous",
            valid_filepaths=[s.file.filepath for s in symbols],
        )
    symbol = symbols[0]
    if filepath:
        if symbol.file.filepath != filepath:
            return RevealSymbolObservation(
                status="error",
                error=f"{symbol_name} not found at {filepath}",
                valid_filepaths=[s.file.filepath for s in symbols],
            )

    # Get dependencies and usages up to specified degree
    dependencies, usages, total_tokens = get_extended_context(symbol, max_depth, max_tokens, collect_dependencies=collect_dependencies, collect_usages=collect_usages)

    was_truncated = max_tokens is not None and total_tokens >= max_tokens

    result = RevealSymbolObservation(
        status="success",
        truncated=was_truncated,
    )
    if collect_dependencies:
        result.dependencies = dependencies
    if collect_usages:
        result.usages = usages
    return result



# ====================================================================
# DOCUMENTATION GENERATION - mdx_docs
# ====================================================================
# Source: mdx_docs_generation.py

import re

from graph_sitter.code_generation.doc_utils.schemas import ClassDoc, MethodDoc, ParameterDoc
from graph_sitter.code_generation.doc_utils.utils import sanitize_html_for_mdx, sanitize_mdx_mintlify_description


def render_mdx_page_for_class(cls_doc: ClassDoc) -> str:
    """Renders the MDX for a single class"""
    return f"""{render_mdx_page_title(cls_doc)}
{render_mdx_inheritence_section(cls_doc)}
{render_mdx_attributes_section(cls_doc)}
{render_mdx_methods_section(cls_doc)}
"""


def render_mdx_page_title(cls_doc: ClassDoc, icon: str | None = None) -> str:
    """Renders the MDX for the page title"""
    page_desc = cls_doc.description if hasattr(cls_doc, "description") else ""

    return f"""---
title: "{cls_doc.title}"
sidebarTitle: "{cls_doc.title}"
icon: "{icon if icon else ""}"
description: "{sanitize_mdx_mintlify_description(page_desc)}"
---
import {{Parameter}} from '/snippets/Parameter.mdx';
import {{ParameterWrapper}} from '/snippets/ParameterWrapper.mdx';
import {{Return}} from '/snippets/Return.mdx';
import {{HorizontalDivider}} from '/snippets/HorizontalDivider.mdx';
import {{GithubLinkNote}} from '/snippets/GithubLinkNote.mdx';
import {{Attribute}} from '/snippets/Attribute.mdx';

<GithubLinkNote link="{cls_doc.github_url}" />
"""


def render_mdx_inheritence_section(cls_doc: ClassDoc) -> str:
    """Renders the MDX for the inheritence section"""
    # Filter on parents who we have docs for
    parents = cls_doc.inherits_from
    if not parents:
        return ""
    parents_string = ", ".join([parse_link(parent) for parent in parents])
    return f"""### Inherits from
{parents_string}
"""


def render_mdx_attributes_section(cls_doc: ClassDoc) -> str:
    """Renders the MDX for the attributes section"""
    sorted_attributes = sorted(cls_doc.attributes + [method for method in cls_doc.methods if method.method_type == "property"], key=lambda x: x.name)
    if len(sorted_attributes) <= 0:
        return ""
    attributes_mdx_string = "\n".join([render_mdx_for_attribute(attribute) for attribute in sorted_attributes])

    return f"""## Attributes
<HorizontalDivider />
{attributes_mdx_string}
"""


def render_mdx_methods_section(cls_doc: ClassDoc) -> str:
    """Renders the MDX for the methods section"""
    sorted_methods = sorted(cls_doc.methods, key=lambda x: x.name)
    if len(sorted_methods) <= 0:
        return ""
    methods_mdx_string = "\n".join([render_mdx_for_method(method) for method in sorted_methods if method.method_type == "method"])

    return f"""## Methods
<HorizontalDivider />
{methods_mdx_string}
"""


def render_mdx_for_attribute(attribute: MethodDoc) -> str:
    """Renders the MDX for a single attribute"""
    attribute_docstring = sanitize_mdx_mintlify_description(attribute.description)
    if len(attribute.return_type) > 0:
        return_type = f"{resolve_type_string(attribute.return_type[0])}"
    else:
        return_type = ""
    if not attribute_docstring:
        attribute_docstring = "\n"
    return f"""### <span className="text-primary">{attribute.name}</span>
<HorizontalDivider light={{true}} />
<Attribute type={{ {return_type if return_type else "<span></span>"} }} description="{attribute_docstring}" />
"""


########################################################################################################################
# METHODS
########################################################################################################################


def format_parameter_for_mdx(parameter: ParameterDoc) -> str:
    type_string = resolve_type_string(parameter.type)
    return f"""
<Parameter
    name="{parameter.name}"
    type={{ {type_string} }}
    description="{sanitize_html_for_mdx(parameter.description)}"
    defaultValue="{sanitize_html_for_mdx(parameter.default)}"
/>
""".strip()


def format_parameters_for_mdx(parameters: list[ParameterDoc]) -> str:
    return "\n".join([format_parameter_for_mdx(parameter) for parameter in parameters])


def format_return_for_mdx(return_type: list[str], return_description: str) -> str:
    description = sanitize_html_for_mdx(return_description) if return_description else ""
    return_type = resolve_type_string(return_type[0])

    return f"""
<Return return_type={{ {return_type} }} description="{description}"/>
"""


def render_mdx_for_method(method: MethodDoc) -> str:
    description = sanitize_mdx_mintlify_description(method.description)
    # =====[ RENDER ]=====
    # TODO add links here
    # TODO add inheritence info here
    mdx_string = f"""### <span className="text-primary">{method.name}</span>
{description}
<GithubLinkNote link="{method.github_url}" />
"""
    if method.parameters:
        mdx_string += f"""
<ParameterWrapper>
{format_parameters_for_mdx(method.parameters)}
</ParameterWrapper>
"""
    if method.return_type:
        mdx_string += f"""
{format_return_for_mdx(method.return_type, method.return_description)}
"""

    return mdx_string


def get_mdx_route_for_class(cls_doc: ClassDoc) -> str:
    """Get the expected MDX route for a class
    split by /core, /python, and /typescript
    """
    lower_class_name = cls_doc.title.lower()
    if lower_class_name.startswith("py"):
        return f"codebase-sdk/python/{cls_doc.title}"
    elif lower_class_name.startswith(("ts", "jsx")):
        return f"codebase-sdk/typescript/{cls_doc.title}"
    else:
        return f"codebase-sdk/core/{cls_doc.title}"


def format_type_string(type_string: str) -> str:
    type_string = type_string.split("|")
    return " | ".join([type_str.strip() for type_str in type_string])


def resolve_type_string(type_string: str) -> str:
    if "<" in type_string:
        return f"<>{parse_link(type_string, href=True)}</>"
    else:
        return f'<code className="text-sm bg-gray-100 px-2 py-0.5 rounded">{format_type_string(type_string)}</code>'


def format_builtin_type_string(type_string: str) -> str:
    if "|" in type_string:
        type_strings = type_string.split("|")
        return " | ".join([type_str.strip() for type_str in type_strings])
    return type_string


def span_type_string_by_pipe(type_string: str) -> str:
    if "|" in type_string:
        type_strings = type_string.split("|")
        return " | ".join([f"<span>{type_str.strip()}</span>" for type_str in type_strings])
    return type_string


def parse_link(type_string: str, href: bool = False) -> str:
    # Match components with angle brackets, handling nested structures

    parts = [p for p in re.split(r"(<[^>]+>)", type_string) if p]

    result = []
    for part in parts:
        if part.startswith("<") and part.endswith(">"):
            # Extract the path from between angle brackets
            path = part[1:-1]
            symbol = path.split("/")[-1]

            # Create a Link object
            link = f'<a href="/{path}" style={{ {{fontWeight: "inherit", fontSize: "inherit"}} }}>{symbol}</a>' if href else f"[{symbol}](/{path})"
            result.append(link)
        else:
            part = format_builtin_type_string(part)
            if href:
                result.append(f"<span>{part.strip()}</span>")
            else:
                result.append(part.strip())

    return " ".join(result)



# ====================================================================
# DOCUMENTATION GENERATION - document_functions
# ====================================================================
# Source: document_functions.py

import graph_sitter
from graph_sitter import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol


def hop_through_imports(imp: Import) -> Symbol | ExternalModule:
    """Finds the root symbol for an import"""
    if isinstance(imp.imported_symbol, Import):
        return hop_through_imports(imp.imported_symbol)
    return imp.imported_symbol


def get_extended_context(symbol: Symbol, degree: int) -> tuple[set[Symbol], set[Symbol]]:
    """Recursively collect dependencies and usages up to the specified degree.

    Args:
        symbol: The symbol to collect context for
        degree: How many levels deep to collect dependencies and usages

    Returns:
        A tuple of (dependencies, usages) where each is a set of related Symbol objects
    """
    dependencies = set()
    usages = set()

    if degree > 0:
        # Collect direct dependencies
        for dep in symbol.dependencies:
            # Hop through imports to find the root symbol
            if isinstance(dep, Import):
                dep = hop_through_imports(dep)

            if isinstance(dep, Symbol) and dep not in dependencies:
                dependencies.add(dep)
                dep_deps, dep_usages = get_extended_context(dep, degree - 1)
                dependencies.update(dep_deps)
                usages.update(dep_usages)

        # Collect usages in the current symbol
        for usage in symbol.usages:
            usage_symbol = usage.usage_symbol
            # Hop through imports for usage symbols too
            if isinstance(usage_symbol, Import):
                usage_symbol = hop_through_imports(usage_symbol)

            if isinstance(usage_symbol, Symbol) and usage_symbol not in usages:
                usages.add(usage_symbol)
                usage_deps, usage_usages = get_extended_context(usage_symbol, degree - 1)
                dependencies.update(usage_deps)
                usages.update(usage_usages)

    return dependencies, usages


@graph_sitter.function("document-functions")
def run(codebase: Codebase):
    # Define the maximum degree of dependencies and usages to consider for context
    N_DEGREE = 2

    # Filter out test and tutorial functions first
    functions = [f for f in codebase.functions if not any(pattern in f.name.lower() for pattern in ["test", "tutorial"]) and not any(pattern in f.filepath.lower() for pattern in ["test", "tutorial"])]

    # Track progress for user feedback
    total_functions = len(functions)
    processed = 0

    print(f"Found {total_functions} functions to process (excluding tests and tutorials)")

    for function in functions:
        processed += 1

        # Skip if already has docstring
        if function.docstring:
            print(f"[{processed}/{total_functions}] Skipping {function.name} - already has docstring")
            continue

        print(f"[{processed}/{total_functions}] Generating docstring for {function.name} at {function.filepath}")

        # Collect context using N-degree dependencies and usages
        dependencies, usages = get_extended_context(function, N_DEGREE)

        # Generate a docstring using the AI with the context
        docstring = codebase.ai(
            """
            Generate a docstring for this function using the provided context.
            The context includes:
            - dependencies: other symbols this function depends on
            - usages: other symbols that use this function
        """,
            target=function,
            # `codebase.ai` is smart about stringifying symbols
            context={"dependencies": list(dependencies), "usages": list(usages)},
        )

        # Set the generated docstring for the function
        if docstring:
            function.set_docstring(docstring)
            print("  ✓ Generated docstring")
        else:
            print("  ✗ Failed to generate docstring")

        # Commit after each function so work is saved incrementally
        # This allows for:
        # 1. Safe early termination - progress won't be lost
        # 2. Immediate feedback - can check results while running
        # 3. Smaller atomic changes - easier to review/revert if needed
        codebase.commit()

    print(f"\nCompleted processing {total_functions} functions")


if __name__ == "__main__":
    print("Parsing codebase...")
    codebase = Codebase.from_repo("fastapi/fastapi", commit="887270ff8a54bb58c406b0651678a27589793d2f")

    print("Running function...")
    run(codebase)



# ====================================================================
# DOCUMENTATION GENERATION - generate_docs_json
# ====================================================================
# Source: generate_docs_json.py

from tqdm import tqdm

from graph_sitter.code_generation.doc_utils.parse_docstring import parse_docstring
from graph_sitter.code_generation.doc_utils.schemas import ClassDoc, GSDocs, MethodDoc
from graph_sitter.code_generation.doc_utils.utils import create_path, extract_class_description, get_type, get_type_str, has_documentation, is_settter, replace_multiple_types
from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.placeholder.placeholder_type import TypePlaceholder

ATTRIBUTES_TO_IGNORE = [
    "ctx",
    "node_id",
    "angular",
    "model_config",
    "constructor_keyword",
    "viz",
    "console",
    "items",
    "node_type",
    "ts_node",
    "file_node_id",
    "statement_type",
    "assignment_types",
]


def generate_docs_json(codebase: Codebase, head_commit: str, raise_on_missing_docstring: bool = False) -> GSDocs:
    """Update documentation table for classes, methods and attributes in the codebase.

    Args:
        codebase (Codebase): the codebase to update the docs for
        head_commit (str): the head commit hash
    Returns:
        dict[str, dict[str, Any]]: the documentation for the codebase
    """
    codegen_sdk_docs = GSDocs(classes=[])
    types_cache = {}

    def process_class_doc(cls):
        """Update or create documentation for a class."""
        description = cls.docstring.source.strip('"""') if cls.docstring else None
        parent_classes = [f"<{create_path(parent)}>" for parent in cls.superclasses if isinstance(parent, Class) and has_documentation(parent)]

        cls_doc = ClassDoc(
            title=cls.name,
            description=extract_class_description(description),
            content=" ",
            path=create_path(cls),
            inherits_from=parent_classes,
            version=str(head_commit),
            github_url=cls.github_url,
        )

        return cls_doc

    def process_method(method, cls, cls_doc, seen_methods):
        """Process a single method and update its documentation."""
        if any(dec.name == "noapidoc" for dec in method.decorators):
            return

        if method.name in seen_methods and not is_settter(method):
            return

        if not method.docstring:
            msg = f"Method {cls.name}.{method.name} does not have a docstring"
            raise ValueError(msg)

        method_path = create_path(method, cls)
        parameters = []

        parsed = parse_docstring(method.docstring.source)
        if parsed is None:
            msg = f"Method {cls.name}.{method.name} docstring does not exist or has incorrect format."
            raise ValueError(msg)

        # Update parameter types
        for param, parsed_param in zip(method.parameters[1:], parsed["arguments"]):
            if param.name == parsed_param.name:
                if isinstance(param.type, TypePlaceholder):
                    resolved_types = []
                else:
                    resolved_types = param.type.resolved_types

                parsed_param.type = replace_multiple_types(
                    codebase=codebase, input_str=parsed_param.type, resolved_types=resolved_types, parent_class=cls, parent_symbol=method, types_cache=types_cache
                )
                if param.default:
                    parsed_param.default = param.default

                parameters.append(parsed_param)
        # Update return type

        if not isinstance(method.return_type, TypePlaceholder):
            return_type = replace_multiple_types(
                codebase=codebase, input_str=method.return_type.source, resolved_types=method.return_type.resolved_types, parent_class=cls, parent_symbol=method, types_cache=types_cache
            )
        else:
            return_type = None
        parsed["return_types"] = [return_type]

        meta_data = {"parent": create_path(method.parent_class), "path": method.file.filepath}
        return MethodDoc(
            name=method.name,
            description=parsed["description"],
            parameters=parsed["arguments"],
            return_type=parsed["return_types"],
            return_description=parsed["return_description"],
            method_type=get_type(method),
            code=method.function_signature,
            path=method_path,
            raises=parsed["raises"],
            metainfo=meta_data,
            version=str(head_commit),
            github_url=method.github_url,
        )

    def process_attribute(attr, cls, cls_doc, seen_methods):
        """Process a single attribute and update its documentation."""
        if attr.name in seen_methods or attr.name in ATTRIBUTES_TO_IGNORE:
            return

        attr_path = create_path(attr, cls)

        description = attr.docstring(attr.parent_class)
        if raise_on_missing_docstring and not description:
            msg = f"Attribute {attr.parent_class.name}.{attr.name} does not have a docstring"
            raise ValueError(msg)
        attr_return_type = []
        if r_type := get_type_str(attr):
            if isinstance(r_type, TypePlaceholder):
                resolved_types = []
            else:
                resolved_types = r_type.resolved_types
            r_type_source = replace_multiple_types(codebase=codebase, input_str=r_type.source, resolved_types=resolved_types, parent_class=cls, parent_symbol=attr, types_cache=types_cache)
            attr_return_type.append(r_type_source)

        attr_info = {"description": description, "attr_return_type": attr_return_type}

        meta_data = {"parent": create_path(attr.parent_class), "path": attr.file.filepath}

        return MethodDoc(
            name=attr.name,
            description=attr_info["description"],
            parameters=[],
            return_type=attr_info["attr_return_type"],
            return_description=None,
            method_type="attribute",
            code=attr.attribute_docstring,
            path=attr_path,
            raises=[],
            metainfo=meta_data,
            version=str(head_commit),
            github_url=attr.github_url,
        )

    # Process all documented classes
    documented_classes = [cls for cls in codebase.classes if has_documentation(cls)]

    for cls in tqdm(documented_classes):
        cls_doc = process_class_doc(cls)
        codegen_sdk_docs.classes.append(cls_doc)
        seen_methods = set()

        # Process methods
        for method in cls.methods(max_depth=None, private=False, magic=False):
            method_doc = process_method(method, cls, cls_doc, seen_methods)
            if not method_doc:
                continue
            seen_methods.add(method_doc.name)
            cls_doc.methods.append(method_doc)

        # Process attributes
        for attr in cls.attributes(max_depth=None, private=False):
            if attr.name in ATTRIBUTES_TO_IGNORE:
                continue

            attr_doc = process_attribute(attr, cls, cls_doc, seen_methods)
            if not attr_doc:
                continue
            seen_methods.add(attr_doc.name)
            cls_doc.attributes.append(attr_doc)

    return codegen_sdk_docs



# ====================================================================
# CODEBASE INTEGRATION - list_directory
# ====================================================================
# Source: list_directory.py

"""Tool for listing directory contents."""

from typing import ClassVar

from langchain_core.messages import ToolMessage
from pydantic import Field

from graph_sitter.extensions.tools.observation import Observation
from graph_sitter.extensions.tools.tool_output_types import ListDirectoryArtifacts
from graph_sitter.sdk.core.codebase import Codebase
from graph_sitter.sdk.core.directory import Directory


class DirectoryInfo(Observation):
    """Information about a directory."""

    name: str = Field(
        description="Name of the directory",
    )
    path: str = Field(
        description="Full path to the directory",
    )
    files: list[str] | None = Field(
        default=None,
        description="List of files in this directory (None if at max depth)",
    )
    subdirectories: list["DirectoryInfo"] = Field(
        default_factory=list,
        description="List of subdirectories",
    )
    is_leaf: bool = Field(
        default=False,
        description="Whether this is a leaf node (at max depth)",
    )
    depth: int = Field(
        default=0,
        description="Current depth in the tree",
    )
    max_depth: int = Field(
        default=1,
        description="Maximum depth allowed",
    )

    str_template: ClassVar[str] = "Directory {path} ({file_count} files, {dir_count} subdirs)"

    def _get_details(self) -> dict[str, int]:
        """Get details for string representation."""
        return {
            "file_count": len(self.files or []),
            "dir_count": len(self.subdirectories),
        }

    def render_as_string(self) -> str:
        """Render directory listing as a file tree."""
        lines = [
            f"[LIST DIRECTORY]: {self.path}",
            "",
        ]

        def add_tree_item(name: str, prefix: str = "", is_last: bool = False) -> tuple[str, str]:
            """Helper to format a tree item with proper prefix."""
            marker = "└── " if is_last else "├── "
            indent = "    " if is_last else "│   "
            return prefix + marker + name, prefix + indent

        def build_tree(items: list[tuple[str, bool, "DirectoryInfo | None"]], prefix: str = "") -> list[str]:
            """Recursively build tree with proper indentation."""
            if not items:
                return []

            result = []
            for i, (name, is_dir, dir_info) in enumerate(items):
                is_last = i == len(items) - 1
                line, new_prefix = add_tree_item(name, prefix, is_last)
                result.append(line)

                # If this is a directory and not a leaf node, show its contents
                if dir_info and not dir_info.is_leaf:
                    subitems = []
                    # Add files first
                    if dir_info.files:
                        for f in sorted(dir_info.files):
                            subitems.append((f, False, None))
                    # Then add subdirectories
                    for d in dir_info.subdirectories:
                        subitems.append((d.name + "/", True, d))

                    result.extend(build_tree(subitems, new_prefix))

            return result

        # Sort files and directories
        items = []
        if self.files:
            for f in sorted(self.files):
                items.append((f, False, None))
        for d in self.subdirectories:
            items.append((d.name + "/", True, d))

        if not items:
            lines.append("(empty directory)")
            return "\n".join(lines)

        # Generate tree
        lines.extend(build_tree(items))

        return "\n".join(lines)

    def to_artifacts(self) -> ListDirectoryArtifacts:
        """Convert directory info to artifacts for UI."""
        artifacts: ListDirectoryArtifacts = {
            "dirpath": self.path,
            "name": self.name,
            "is_leaf": self.is_leaf,
            "depth": self.depth,
            "max_depth": self.max_depth,
        }

        if self.files is not None:
            artifacts["files"] = self.files
            artifacts["file_paths"] = [f"{self.path}/{f}" for f in self.files]

        if self.subdirectories:
            artifacts["subdirs"] = [d.name for d in self.subdirectories]
            artifacts["subdir_paths"] = [d.path for d in self.subdirectories]

        return artifacts


class ListDirectoryObservation(Observation):
    """Response from listing directory contents."""

    directory_info: DirectoryInfo = Field(
        description="Information about the directory",
    )

    str_template: ClassVar[str] = "{directory_info}"

    def render(self, tool_call_id: str) -> ToolMessage:
        """Render directory listing with artifacts for UI."""
        if self.status == "error":
            error_artifacts: ListDirectoryArtifacts = {
                "dirpath": self.directory_info.path,
                "name": self.directory_info.name,
                "error": self.error,
            }
            return ToolMessage(
                content=f"[ERROR LISTING DIRECTORY]: {self.directory_info.path}: {self.error}",
                status=self.status,
                name="list_directory",
                artifact=error_artifacts,
                tool_call_id=tool_call_id,
            )

        return ToolMessage(
            content=self.directory_info.render_as_string(),
            status=self.status,
            name="list_directory",
            artifact=self.directory_info.to_artifacts(),
            tool_call_id=tool_call_id,
        )


def list_directory(codebase: Codebase, path: str = "./", depth: int = 2) -> ListDirectoryObservation:
    """List contents of a directory.

    Args:
        codebase: The codebase to operate on
        path: Path to directory relative to workspace root
        depth: How deep to traverse the directory tree. Default is 1 (immediate children only).
               Use -1 for unlimited depth.
    """
    try:
        directory = codebase.get_directory(path)
    except ValueError:
        return ListDirectoryObservation(
            status="error",
            error=f"Directory not found: {path}",
            directory_info=DirectoryInfo(
                status="error",
                name=path.split("/")[-1],
                path=path,
                files=[],
                subdirectories=[],
            ),
        )

    def get_directory_info(dir_obj: Directory, current_depth: int, max_depth: int) -> DirectoryInfo:
        """Helper function to get directory info recursively."""
        # Get direct files (always include files unless at max depth)
        all_files = []
        for file_name in dir_obj.file_names:
            all_files.append(file_name)

        # Get direct subdirectories
        subdirs = []
        for subdir in dir_obj.subdirectories(recursive=True):
            # Only include direct descendants
            if subdir.parent == dir_obj:
                if current_depth > 1 or current_depth == -1:
                    # For deeper traversal, get full directory info
                    new_depth = current_depth - 1 if current_depth > 1 else -1
                    subdirs.append(get_directory_info(subdir, new_depth, max_depth))
                else:
                    # At max depth, return a leaf node
                    subdirs.append(
                        DirectoryInfo(
                            status="success",
                            name=subdir.name,
                            path=subdir.dirpath,
                            files=None,  # Don't include files at max depth
                            is_leaf=True,
                            depth=current_depth,
                            max_depth=max_depth,
                        )
                    )

        return DirectoryInfo(
            status="success",
            name=dir_obj.name,
            path=dir_obj.dirpath,
            files=sorted(all_files),
            subdirectories=subdirs,
            depth=current_depth,
            max_depth=max_depth,
        )

    dir_info = get_directory_info(directory, depth, depth)
    return ListDirectoryObservation(
        status="success",
        directory_info=dir_info,
    )



# ====================================================================
# CODEBASE INTEGRATION - current_code_codebase
# ====================================================================
# Source: current_code_codebase.py

# TODO: move out of graph sitter, useful for other projects

import importlib
from pathlib import Path
from typing import TypedDict

from graph_sitter.codebase.config import ProjectConfig
from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.configs.models.secrets import SecretsConfig
from graph_sitter.core.codebase import Codebase, CodebaseType
from graph_sitter.git.repo_operator.repo_operator import RepoOperator
from graph_sitter.git.schemas.repo_config import RepoConfig
from graph_sitter.shared.decorators.docs import DocumentedObject, apidoc_objects, no_apidoc_objects, py_apidoc_objects, ts_apidoc_objects
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def get_graphsitter_repo_path() -> str:
    """Points to base directory of the Graph-sitter repo (.git) that is currently running"""
    import graph_sitter as sdk

    filepath = sdk.__file__
    codegen_base_dir = filepath.replace("/graph_sitter/__init__.py", "")
    codegen_base_dir = codegen_base_dir.replace("/src", "")
    return codegen_base_dir


def get_codegen_codebase_base_path() -> str:
    import graph_sitter as sdk

    filepath = sdk.__file__
    codegen_base_dir = filepath.replace("/graph_sitter/__init__.py", "")
    return "src" if "src" in codegen_base_dir else ""


def get_current_code_codebase(config: CodebaseConfig | None = None, secrets: SecretsConfig | None = None, subdirectories: list[str] | None = None) -> CodebaseType:
    """Returns a Codebase for the code that is *currently running* (i.e. the Graph-sitter repo)"""
    codegen_repo_path = get_graphsitter_repo_path()
    base_dir = get_codegen_codebase_base_path()
    logger.info(f"Creating codebase from repo at: {codegen_repo_path} with base_path {base_dir}")

    repo_config = RepoConfig.from_repo_path(codegen_repo_path)
    repo_config.respect_gitignore = False
    op = RepoOperator(repo_config=repo_config, bot_commit=False)

    config = (config or CodebaseConfig()).model_copy(update={"base_path": base_dir})
    projects = [ProjectConfig(repo_operator=op, programming_language=ProgrammingLanguage.PYTHON, subdirectories=subdirectories, base_path=base_dir)]
    codebase = Codebase(projects=projects, config=config, secrets=secrets)
    return codebase


def import_all_codegen_sdk_modules():
    # for file in codegen.sdk:

    CODEGEN_SDK_DIR = Path(get_graphsitter_repo_path())
    if base := get_codegen_codebase_base_path():
        CODEGEN_SDK_DIR /= base
    CODEGEN_SDK_DIR /= "graph_sitter"
    for file in CODEGEN_SDK_DIR.rglob("*.py"):
        relative_path = file.relative_to(CODEGEN_SDK_DIR)
        # ignore braintrust_evaluator because it runs stuff on import
        if "__init__" in file.name or "braintrust_evaluator" in file.name:
            continue
        module_name = "graph_sitter." + str(relative_path).replace("/", ".").removesuffix(".py")
        try:
            importlib.import_module(module_name)
        except Exception as e:
            print(f"Error importing {module_name}: {e}")


class DocumentedObjects(TypedDict):
    apidoc: list[DocumentedObject]
    ts_apidoc: list[DocumentedObject]
    py_apidoc: list[DocumentedObject]
    no_apidoc: list[DocumentedObject]


def get_documented_objects() -> DocumentedObjects:
    """Get all the objects decorated with apidoc, py_apidoc, ts_apidoc, and no_apidoc decorators,
    by importing all codegen.sdk modules and keeping track of decorated objects at import time using
    the respective decorators
    """
    import_all_codegen_sdk_modules()
    from graph_sitter.core.codebase import CodebaseType, PyCodebaseType, TSCodebaseType

    if PyCodebaseType not in apidoc_objects:
        apidoc_objects.append(DocumentedObject(name="PyCodebaseType", module="graph_sitter.core.codebase", object=PyCodebaseType))
    if TSCodebaseType not in apidoc_objects:
        apidoc_objects.append(DocumentedObject(name="TSCodebaseType", module="graph_sitter.core.codebase", object=TSCodebaseType))
    if CodebaseType not in apidoc_objects:
        apidoc_objects.append(DocumentedObject(name="CodebaseType", module="graph_sitter.core.codebase", object=CodebaseType))
    return {"apidoc": apidoc_objects, "py_apidoc": py_apidoc_objects, "ts_apidoc": ts_apidoc_objects, "no_apidoc": no_apidoc_objects}



# ====================================================================
# CODEBASE INTEGRATION - codegen_sdk_codebase
# ====================================================================
# Source: codegen_sdk_codebase.py

import os.path

from graph_sitter.code_generation.current_code_codebase import get_codegen_codebase_base_path, get_current_code_codebase, get_graphsitter_repo_path
from graph_sitter.core.codebase import Codebase


def get_codegen_sdk_subdirectories() -> list[str]:
    base = get_codegen_codebase_base_path()
    graphsitter_path = os.path.join(base, "graph_sitter")
    paths = [os.path.join(base, "codemods")]
    for dir in os.listdir(os.path.join(get_graphsitter_repo_path(), graphsitter_path)):
        if dir in ["git", "extensions", "cli"]:
            continue
        paths.append(os.path.join(graphsitter_path, dir))

    return paths


def get_codegen_sdk_codebase() -> Codebase:
    """Grabs a Codebase w/ GraphSitter content. Responsible for figuring out where it is, e.g. in Modal or local"""
    codebase = get_current_code_codebase(subdirectories=get_codegen_sdk_subdirectories())
    return codebase



# ====================================================================
# PUBLIC API
# ====================================================================

__all__ = [
    # Symbol tools
    "reveal_symbol", "get_symbol_info", "hop_through_imports",
    "RevealSymbolTool", "RevealSymbolInput", "SymbolInfo",
    # Documentation tools  
    "render_mdx_page_for_class", "generate_docs_json", "run",
    # Codebase tools
    "list_directory", "get_current_code_codebase", "get_codegen_sdk_codebase",
]
