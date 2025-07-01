
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from graph_sitter.codebase.progress.task import Task

if TYPE_CHECKING:

T = TypeVar("T", bound="Task")

class Progress(ABC, Generic[T]):
    @abstractmethod
    def begin(self, message: str, count: int | None = None) -> T:
        pass
