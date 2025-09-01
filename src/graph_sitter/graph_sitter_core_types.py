"""
Core types for the graph-sitter library.

This module provides a centralized import point for all core types used in graph-sitter.
"""

from __future__ import annotations

# Import all the types requested
try:
    from graph_sitter.core.detached_symbols.argument import Argument
except ImportError:
    from graph_sitter.python.detached_symbols.argument import Argument

try:
    from graph_sitter.core.assignment import Assignment
except ImportError:
    from graph_sitter.python.assignment import Assignment

try:
    from graph_sitter.core.statements.assignment_statement import AssignmentStatement
except ImportError:
    from graph_sitter.python.statements.assignment_statement import AssignmentStatement

try:
    from graph_sitter.core.statements.attribute import Attribute
except ImportError:
    from graph_sitter.python.statements.attribute import Attribute

try:
    from graph_sitter.core.expressions.await_expression import AwaitExpression
except ImportError:
    from graph_sitter.python.expressions.await_expression import AwaitExpression

try:
    from graph_sitter.core.expressions.binary_expression import BinaryExpression
except ImportError:
    from graph_sitter.python.expressions.binary_expression import BinaryExpression

try:
    from graph_sitter.core.statements.block_statement import BlockStatement
except ImportError:
    from graph_sitter.python.statements.block_statement import BlockStatement

try:
    from graph_sitter.core.expressions.boolean import Boolean
except ImportError:
    from graph_sitter.python.expressions.boolean import Boolean

from graph_sitter.core.interfaces.callable import Callable

try:
    from graph_sitter.core.statements.catch_statement import CatchStatement
except ImportError:
    from graph_sitter.python.statements.catch_statement import CatchStatement

try:
    from graph_sitter.core.expressions.chained_attribute import ChainedAttribute
except ImportError:
    from graph_sitter.python.expressions.chained_attribute import ChainedAttribute

try:
    from graph_sitter.core.class_definition import Class
except ImportError:
    from graph_sitter.python.class_definition import Class

try:
    from graph_sitter.core.expressions.code_block import CodeBlock
except ImportError:
    from graph_sitter.python.expressions.code_block import CodeBlock

from graph_sitter.core.codeowner import CodeOwner
from graph_sitter.core.codebase import Codebase

try:
    from graph_sitter.core.expressions.comment import Comment
except ImportError:
    from graph_sitter.python.expressions.comment import Comment

try:
    from graph_sitter.core.expressions.comment_group import CommentGroup
except ImportError:
    from graph_sitter.python.expressions.comment_group import CommentGroup

try:
    from graph_sitter.core.expressions.comparison_expression import ComparisonExpression
except ImportError:
    from graph_sitter.python.expressions.comparison_expression import ComparisonExpression

try:
    from graph_sitter.core.expressions.decorator import Decorator
except ImportError:
    from graph_sitter.python.expressions.decorator import Decorator

try:
    from graph_sitter.core.expressions.dict import Dict
except ImportError:
    from graph_sitter.python.expressions.dict import Dict

from graph_sitter.core.directory import Directory
from graph_sitter.core.interfaces.editable import Editable
from graph_sitter.core.export import Export

try:
    from graph_sitter.core.statements.export_statement import ExportStatement
except ImportError:
    from graph_sitter.typescript.statements.export_statement import ExportStatement

from graph_sitter.core.interfaces.exportable import Exportable

try:
    from graph_sitter.core.expressions.expression import Expression
except ImportError:
    from graph_sitter.python.expressions.expression import Expression

try:
    from graph_sitter.core.expressions.expression_group import ExpressionGroup
except ImportError:
    from graph_sitter.python.expressions.expression_group import ExpressionGroup

try:
    from graph_sitter.core.statements.expression_statement import ExpressionStatement
except ImportError:
    from graph_sitter.python.statements.expression_statement import ExpressionStatement

from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.file import File
from graph_sitter.codebase.flagging.enums import FlagKwargs

try:
    from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
except ImportError:
    from graph_sitter.python.statements.for_loop_statement import ForLoopStatement

from graph_sitter.core.function import Function

try:
    from graph_sitter.core.detached_symbols.function_call import FunctionCall
except ImportError:
    from graph_sitter.python.detached_symbols.function_call import FunctionCall

try:
    from graph_sitter.core.expressions.generic_type import GenericType
except ImportError:
    from graph_sitter.python.expressions.generic_type import GenericType

from graph_sitter.core.interfaces.has_block import HasBlock
from graph_sitter.core.interfaces.has_name import HasName
from graph_sitter.core.interfaces.has_value import HasValue

try:
    from graph_sitter.core.statements.if_block_statement import IfBlockStatement
except ImportError:
    from graph_sitter.python.statements.if_block_statement import IfBlockStatement

from graph_sitter.core.import_resolution import Import

try:
    from graph_sitter.core.statements.import_statement import ImportStatement
except ImportError:
    from graph_sitter.python.statements.import_statement import ImportStatement

from graph_sitter.core.interfaces.importable import Importable, ImportType
from graph_sitter.core.interface import Interface

try:
    from graph_sitter.core.expressions.list import List
except ImportError:
    from graph_sitter.python.expressions.list import List

try:
    from graph_sitter.extensions.lsp.protocol.lsp_types import MessageType
except ImportError:
    # Define a placeholder if not available
    class MessageType:
        """Placeholder for MessageType if not available."""
        pass

try:
    from graph_sitter.core.expressions.multi_expression import MultiExpression
except ImportError:
    from graph_sitter.python.expressions.multi_expression import MultiExpression

try:
    from graph_sitter.core.expressions.multi_line_collection import MultiLineCollection
except ImportError:
    from graph_sitter.python.expressions.multi_line_collection import MultiLineCollection

try:
    from graph_sitter.core.expressions.name import Name
except ImportError:
    from graph_sitter.python.expressions.name import Name

try:
    from graph_sitter.core.expressions.named_type import NamedType
except ImportError:
    from graph_sitter.python.expressions.named_type import NamedType

try:
    from graph_sitter.core.expressions.none_type import NoneType
except ImportError:
    from graph_sitter.python.expressions.none_type import NoneType

try:
    from graph_sitter.core.expressions.number import Number
except ImportError:
    from graph_sitter.python.expressions.number import Number

try:
    from graph_sitter.core.expressions.pair import Pair
except ImportError:
    from graph_sitter.python.expressions.pair import Pair

try:
    from graph_sitter.core.expressions.parameter import Parameter
except ImportError:
    from graph_sitter.python.expressions.parameter import Parameter

try:
    from graph_sitter.core.expressions.parenthesized_expression import ParenthesizedExpression
except ImportError:
    from graph_sitter.python.expressions.parenthesized_expression import ParenthesizedExpression

from graph_sitter.core.placeholder.placeholder import Placeholder
from graph_sitter.core.placeholder.placeholder_type import PlaceholderType

try:
    from graph_sitter.core.statements.raise_statement import RaiseStatement
except ImportError:
    from graph_sitter.python.statements.raise_statement import RaiseStatement

try:
    from graph_sitter.core.statements.return_statement import ReturnStatement
except ImportError:
    from graph_sitter.python.statements.return_statement import ReturnStatement

from graph_sitter.core.file import SourceFile
from graph_sitter.codebase.span import Span

try:
    from graph_sitter.core.statements.statement import Statement, StatementType
except ImportError:
    from graph_sitter.python.statements.statement import Statement, StatementType

try:
    from graph_sitter.core.expressions.string import String
except ImportError:
    from graph_sitter.python.expressions.string import String

from graph_sitter.core.placeholder.stub_placeholder import StubPlaceholder

try:
    from graph_sitter.core.expressions.subscript_expression import SubscriptExpression
except ImportError:
    from graph_sitter.python.expressions.subscript_expression import SubscriptExpression

try:
    from graph_sitter.core.statements.switch_case import SwitchCase
except ImportError:
    from graph_sitter.typescript.statements.switch_case import SwitchCase

try:
    from graph_sitter.core.statements.switch_statement import SwitchStatement
except ImportError:
    from graph_sitter.typescript.statements.switch_statement import SwitchStatement

from graph_sitter.core.symbol import Symbol
from graph_sitter.core.symbol_group import SymbolGroup

try:
    from graph_sitter.core.statements.symbol_statement import SymbolStatement
except ImportError:
    from graph_sitter.python.statements.symbol_statement import SymbolStatement

try:
    from graph_sitter.core.expressions.ternary_expression import TernaryExpression
except ImportError:
    from graph_sitter.python.expressions.ternary_expression import TernaryExpression

try:
    from graph_sitter.core.statements.try_catch_statement import TryCatchStatement
except ImportError:
    from graph_sitter.python.statements.try_catch_statement import TryCatchStatement

try:
    from graph_sitter.core.expressions.tuple import Tuple
except ImportError:
    from graph_sitter.python.expressions.tuple import Tuple

try:
    from graph_sitter.core.expressions.tuple_type import TupleType
except ImportError:
    from graph_sitter.python.expressions.tuple_type import TupleType

try:
    from graph_sitter.core.expressions.type import Type
except ImportError:
    from graph_sitter.python.expressions.type import Type

from graph_sitter.core.type_alias import TypeAlias
from graph_sitter.core.placeholder.type_placeholder import TypePlaceholder
from graph_sitter.core.interfaces.typeable import Typeable

try:
    from graph_sitter.core.expressions.unary_expression import UnaryExpression
except ImportError:
    from graph_sitter.python.expressions.unary_expression import UnaryExpression

try:
    from graph_sitter.core.expressions.union_type import UnionType
except ImportError:
    from graph_sitter.python.expressions.union_type import UnionType

try:
    from graph_sitter.core.expressions.unpack import Unpack
except ImportError:
    from graph_sitter.python.expressions.unpack import Unpack

from graph_sitter.core.interfaces.unwrappable import Unwrappable
from graph_sitter.core.interfaces.usable import Usable
from graph_sitter.core.dataclasses.usage import Usage, UsageKind, UsageType

try:
    from graph_sitter.core.expressions.value import Value
except ImportError:
    from graph_sitter.python.expressions.value import Value

try:
    from graph_sitter.core.statements.while_statement import WhileStatement
except ImportError:
    from graph_sitter.python.statements.while_statement import WhileStatement

try:
    from graph_sitter.core.statements.with_statement import WithStatement
except ImportError:
    from graph_sitter.python.statements.with_statement import WithStatement

# Export all the types
__all__ = [
    "Argument",
    "Assignment",
    "AssignmentStatement",
    "Attribute",
    "AwaitExpression",
    "BinaryExpression",
    "BlockStatement",
    "Boolean",
    "Callable",
    "CatchStatement",
    "ChainedAttribute",
    "Class",
    "CodeBlock",
    "CodeOwner",
    "Codebase",
    "Comment",
    "CommentGroup",
    "ComparisonExpression",
    "Decorator",
    "Dict",
    "Directory",
    "Editable",
    "Export",
    "ExportStatement",
    "Exportable",
    "Expression",
    "ExpressionGroup",
    "ExpressionStatement",
    "ExternalModule",
    "File",
    "FlagKwargs",
    "ForLoopStatement",
    "Function",
    "FunctionCall",
    "GenericType",
    "HasBlock",
    "HasName",
    "HasValue",
    "IfBlockStatement",
    "Import",
    "ImportStatement",
    "ImportType",
    "Importable",
    "Interface",
    "List",
    "MessageType",
    "MultiExpression",
    "MultiLineCollection",
    "Name",
    "NamedType",
    "NoneType",
    "Number",
    "Pair",
    "Parameter",
    "ParenthesizedExpression",
    "Placeholder",
    "PlaceholderType",
    "RaiseStatement",
    "ReturnStatement",
    "SourceFile",
    "Span",
    "Statement",
    "StatementType",
    "String",
    "StubPlaceholder",
    "SubscriptExpression",
    "SwitchCase",
    "SwitchStatement",
    "Symbol",
    "SymbolGroup",
    "SymbolStatement",
    "TernaryExpression",
    "TryCatchStatement",
    "Tuple",
    "TupleType",
    "Type",
    "TypeAlias",
    "TypePlaceholder",
    "Typeable",
    "UnaryExpression",
    "UnionType",
    "Unpack",
    "Unwrappable",
    "Usable",
    "Usage",
    "UsageKind",
    "UsageType",
    "Value",
    "WhileStatement",
    "WithStatement",
]

