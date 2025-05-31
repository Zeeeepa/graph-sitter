from contexten.extensions.lsp.codemods.base import CodeAction
from contexten.extensions.lsp.codemods.split_tests import SplitTests

ACTIONS: list[CodeAction] = [SplitTests()]
