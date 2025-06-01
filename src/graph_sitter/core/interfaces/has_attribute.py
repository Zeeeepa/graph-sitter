
from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from graph_sitter.core.interfaces.editable import Editable

if TYPE_CHECKING:

Attribute = TypeVar("Attribute", bound="Editable")

class HasAttribute(Generic[Attribute]):
    @abstractmethod
    def resolve_attribute(self, name: str) -> Attribute | None:
        """Resolve an attribute belonging to this object."""
        pass
