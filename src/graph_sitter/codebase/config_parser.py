
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from graph_sitter.codebase.codebase_context import CodebaseContext
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage
from graph_sitter.typescript.config_parser import TSConfigParser

if TYPE_CHECKING:

class ConfigParser(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def parse_configs(self, codebase_context: "CodebaseContext"): ...

def get_config_parser_for_language(language: ProgrammingLanguage, codebase_context: "CodebaseContext") -> ConfigParser | None:

    if language == ProgrammingLanguage.TYPESCRIPT:
        return TSConfigParser(codebase_context)

    return None
