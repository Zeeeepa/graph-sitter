
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from graph_sitter.codebase.codebase_context import CodebaseContext

if TYPE_CHECKING:

class Parseable(ABC):
    @abstractmethod
    def parse(self, ctx: "CodebaseContext") -> None:
        """Adds itself and its children to the codebase graph."""
