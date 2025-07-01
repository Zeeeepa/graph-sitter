
from graph_sitter.codebase.config import TestFlags
from graph_sitter.codebase.factory.get_session import get_codebase_session

if TYPE_CHECKING:
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.import_resolution import Import, ImportResolution


def test_import_properties_basic(tmpdir) -> None:
    # language=python
    content = """
import a
import b.c as C
from d.e import f as F
import a.b.c
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        z = file.imports
        assert len(z) == 4
        assert z[0].source == "import a"
        assert z[0].module.source == "a"
        assert z[0].symbol_name.source == "a"
        assert z[0].alias.source == "a"

        assert z[1].source == "import b.c as C"
        assert z[1].module.source == "b.c"
        assert z[1].symbol_name.source == "b.c"
        assert z[1].alias.source == "C"

        assert z[2].source == "from d.e import f as F"
        assert z[2].module.source == "d.e"
        assert z[2].symbol_name.source == "f"
        assert z[2].alias.source == "F"

        assert z[3].source == "import a.b.c"
        assert z[3].module.source == "a.b.c"
        assert z[3].symbol_name.source == "a.b.c"
        assert z[3].alias.source == "a.b.c"


def test_import_properties(tmpdir) -> None:
    # language=python
    content = """
import x
import a.b.c
from a import b
from b.c import d
from e.f import g as h
from e.f.g import (i as j, k as l, m as n)
import x.y.z.foo as foo_bar # toughie
"""

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # =====[ Look at the objects ]=====
        imports = file.imports
        assert len(imports) == 9
        aliases = [x.alias.source for x in imports]
        assert "x" in aliases
        assert "a.b.c" in aliases
        assert "b" in aliases
        assert "d" in aliases
        assert "h" in aliases
        assert "g" not in aliases
        assert "i" not in aliases
        assert "j" in aliases
        assert "k" not in aliases
        assert "l" in aliases
        assert "m" not in aliases
        assert "n" in aliases
        assert "foo_bar" in aliases

        # =====[ Test equality ]=====
        imports = file.imports
        assert file == file
        assert imports[0] == imports[0]
        assert imports[0] != imports[1]


def test_import_properties_multi_imports(tmpdir) -> None:
    # language=python
    content = """
import a
from a.b.c import g
from a.b.c import (
    e,
    f,
)
from a.b import (
    d,
    e as E,
    f as F
)
import a as A
"""

    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        z = file.imports
        assert set(i.alias.source for i in file.imports) == {"a", "g", "e", "d", "E", "F", "A", "f"}
        assert len(z) > 0

        # =====[ "import a" ]=====
        assert z[0].source == "import a"

        # =====[ "from a.b.c import d" ]=====
        assert z[1].source == "from a.b.c import g"
        assert z[1].module.source == "a.b.c"
        assert z[1].symbol_name.source == "g"

        # =====[ "from a.b.c import (e, f)" ]=====
        assert (
            z[2].source
            == """from a.b.c import (
    e,
    f,
)"""
        )
        assert z[2].module.source == "a.b.c"
        assert z[2].symbol_name.source == "e"

        # =====[ "from a.b.c import (e, f)" ]=====
        assert z[3].module.source == "a.b.c"
        assert z[3].symbol_name.source == "f"
        assert (
            z[3].source
            == """from a.b.c import (
    e,
    f,
)"""
        )

        # =====[ "from a.b import (d, e as E, f as F)" ]=====
        assert (
            z[4].source
            == """from a.b import (
    d,
    e as E,
    f as F
)"""
        )
        assert z[4].module.source == "a.b"
        assert z[4].symbol_name.source == "d"
        assert z[4].alias.source == "d"
        assert (
            z[5].source
            == """from a.b import (
    d,
    e as E,
    f as F
)"""
        )
        assert z[5].module.source == "a.b"
        assert z[5].symbol_name.source == "e"
        assert z[5].alias.source == "E"
        assert (
            z[6].source
            == """from a.b import (
    d,
    e as E,
    f as F
)"""
        )
        assert z[6].module.source == "a.b"
        assert z[6].symbol_name.source == "f"
        assert z[6].alias.source == "F"

        # =====[ import a as A ]=====
        assert z[7].source == "import a as A"
        assert z[7].module.source == "a"
        assert z[7].symbol_name.source == "a"
        assert z[7].alias.source == "A"


def test_import_resolution_file_import(tmpdir: str) -> None:
    """Tests function.usages returns usages from file imports"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a/b/c/src.py": """
def update():
    pass
""",
            "consumer.py": """
from a.b.c import src as operations

def func():
    operations.update()
""",
        },
    ) as codebase:
        src_file: SourceFile = codebase.get_file("a/b/c/src.py")
        consumer_file: SourceFile = codebase.get_file("consumer.py")

        # =====[ Imports & Resolution ]=====
        assert len(consumer_file.imports) == 1
        src_import: Import = consumer_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True

        # =====[ Look at call-sites ]=====
        update = src_file.get_function("update")
        call_sites = update.call_sites
        assert len(call_sites) == 1
        call_site = call_sites[0]
        assert call_site.file == consumer_file


def test_import_resolution_file_syspath_inactive(tmpdir: str, monkeypatch) -> None:
    """Tests function.usages returns usages from file imports"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a/b/c/src.py": """
def update():
    pass
""",
            "consumer.py": """
from b.c import src as operations

def func():
    operations.update()
""",
        },
    ) as codebase:
        src_file: SourceFile = codebase.get_file("a/b/c/src.py")
        consumer_file: SourceFile = codebase.get_file("consumer.py")

        # Disable resolution via sys.path
        codebase.ctx.config.py_resolve_syspath = False

        # =====[ Imports cannot be found without sys.path being set and not active ]=====
        assert len(consumer_file.imports) == 1
        src_import: Import = consumer_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution is None

        # Modify sys.path for this test only
        monkeypatch.syspath_prepend("a")

        # =====[ Imports cannot be found with sys.path set but not active ]=====
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution is None


def test_import_resolution_file_syspath_active(tmpdir: str, monkeypatch) -> None:
    """Tests function.usages returns usages from file imports"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a/b/c/src.py": """
def update():
    pass
""",
            "consumer.py": """
from b.c import src as operations

def func():
    operations.update()
""",
        },
    ) as codebase:
        src_file: SourceFile = codebase.get_file("a/b/c/src.py")
        consumer_file: SourceFile = codebase.get_file("consumer.py")

        # Enable resolution via sys.path
        codebase.ctx.config.py_resolve_syspath = True
        # Allow resolving files and modules outside of the repo path
        codebase.ctx.config.allow_external = True

        # =====[ Imports cannot be found without sys.path being set ]=====
        assert len(consumer_file.imports) == 1
        src_import: Import = consumer_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution is None

        # Modify sys.path for this test only
        monkeypatch.syspath_prepend("a")

        # =====[ Imports can be found with sys.path set and active ]=====
        codebase.ctx.config.py_resolve_syspath = True
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True


def test_import_resolution_file_custom_resolve_path(tmpdir: str) -> None:
    """Tests function.usages returns usages from file imports"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a/b/c/src.py": """
def update():
    pass
""",
            "consumer.py": """
from b.c import src as operations
from c import src as operations2

def func():
    operations.update()
""",
        },
    ) as codebase:
        src_file: SourceFile = codebase.get_file("a/b/c/src.py")
        consumer_file: SourceFile = codebase.get_file("consumer.py")

        # =====[ Imports cannot be found without custom resolve path being set ]=====
        assert len(consumer_file.imports) == 2
        src_import: Import = consumer_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution is None

        # =====[ Imports cannot be found with custom resolve path set to invalid path ]=====
        codebase.ctx.config.import_resolution_paths = ["x"]
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution is None

        # =====[ Imports can be found with custom resolve path set ]=====
        codebase.ctx.config.import_resolution_paths = ["a"]
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True

        # =====[ Imports can be found with custom resolve multi-path set ]=====
        src_import = consumer_file.imports[1]
        codebase.ctx.config.import_resolution_paths = ["a/b"]
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True


def test_import_resolution_file_custom_resolve_and_syspath_precedence(tmpdir: str, monkeypatch) -> None:
    """Tests function.usages returns usages from file imports"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a/c/src.py": """
def update1():
    pass
""",
            "a/b/c/src.py": """
def update2():
    pass
""",
            "consumer.py": """
from c import src as operations

def func():
    operations.update2()
""",
        },
    ) as codebase:
        src_file: SourceFile = codebase.get_file("a/b/c/src.py")
        consumer_file: SourceFile = codebase.get_file("consumer.py")

        # Ensure we don't have overrites and enable syspath resolution
        codebase.ctx.config.import_resolution_paths = []
        codebase.ctx.config.py_resolve_syspath = True
        # Allow resolving files and modules outside of the repo path
        codebase.ctx.config.allow_external = True

        # =====[ Import with sys.path set can be found ]=====
        assert len(consumer_file.imports) == 1
        # Modify sys.path for this test only
        monkeypatch.syspath_prepend("a")
        src_import: Import = consumer_file.imports[0]
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file.file_path == "a/c/src.py"

        # =====[ Imports can be found with custom resolve over sys.path ]=====
        codebase.ctx.config.import_resolution_paths = ["a/b"]
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True


def test_import_resolution_default_conflicts_overrite(tmpdir: str, monkeypatch) -> None:
    """Tests function.usages returns usages from file imports"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a/src.py": """
def update1():
    pass
""",
            "b/a/src.py": """
def update2():
    pass
""",
            "consumer.py": """
from a import src as operations

def func():
    operations.update2()
""",
        },
    ) as codebase:
        src_file: SourceFile = codebase.get_file("a/src.py")
        src_file_overrite: SourceFile = codebase.get_file("b/a/src.py")
        consumer_file: SourceFile = codebase.get_file("consumer.py")

        # Ensure we don't have overrites and enable syspath resolution
        codebase.ctx.config.import_resolution_paths = []
        codebase.ctx.config.py_resolve_syspath = True
        # Allow resolving files and modules outside of the repo path
        codebase.ctx.config.allow_external = True

        # =====[ Default import works ]=====
        assert len(consumer_file.imports) == 1
        src_import: Import = consumer_file.imports[0]
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file

        # =====[ Sys.path overrite has precedence ]=====
        monkeypatch.syspath_prepend("b")
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is not src_file
        assert src_import_resolution.from_file is src_file_overrite

        # =====[ Custom overrite has precedence ]=====
        codebase.ctx.config.import_resolution_paths = ["b"]
        src_import_resolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is not src_file
        assert src_import_resolution.from_file is src_file_overrite


def test_import_resolution_init_wildcard(tmpdir: str) -> None:
    """Tests that named import from a file with wildcard resolves properly"""
    # language=python
    content1 = """TEST_CONST=2
    foo=9
    """
    content2 = """from testdir.test1 import *
    bar=foo
    test=TEST_CONST"""
    content3 = """from testdir import TEST_CONST
    test3=TEST_CONST"""
    with get_codebase_session(tmpdir=tmpdir, files={"testdir/test1.py": content1, "testdir/__init__.py": content2, "test3.py": content3}) as codebase:
        file1: SourceFile = codebase.get_file("testdir/test1.py")
        file2: SourceFile = codebase.get_file("testdir/__init__.py")
        file3: SourceFile = codebase.get_file("test3.py")

        symb = file1.get_symbol("TEST_CONST")
        test = file2.get_symbol("test")
        test3 = file3.get_symbol("test3")
        test3_import = file3.get_import("TEST_CONST")

        assert len(symb.usages) == 3
        assert symb.symbol_usages == [test, test3, test3_import]


def test_import_resolution_wildcard_func(tmpdir: str) -> None:
    """Tests that named import from a file with wildcard resolves properly"""
    # language=python
    content1 = """
    def foo():
        pass
    def bar():
        pass
    """
    content2 = """
    from testa import *

    foo()
    """

    with get_codebase_session(tmpdir=tmpdir, files={"testa.py": content1, "testb.py": content2}) as codebase:
        testa: SourceFile = codebase.get_file("testa.py")
        testb: SourceFile = codebase.get_file("testb.py")

        foo = testa.get_symbol("foo")
        bar = testa.get_symbol("bar")
        assert len(foo.usages) == 1
        assert len(foo.call_sites) == 1

        assert len(bar.usages) == 0
        assert len(bar.call_sites) == 0
        assert len(testb.function_calls) == 1


def test_import_resolution_chaining_wildcards(tmpdir: str) -> None:
    """Tests that chaining wildcard imports resolves properly"""
    # language=python
    content1 = """TEST_CONST=2
    foo=9
    """
    content2 = """from testdir.test1 import *
    bar=foo
    test=TEST_CONST"""
    content3 = """from testdir import *
    test3=TEST_CONST"""
    with get_codebase_session(tmpdir=tmpdir, files={"testdir/test1.py": content1, "testdir/__init__.py": content2, "test3.py": content3}) as codebase:
        file1: SourceFile = codebase.get_file("testdir/test1.py")
        file2: SourceFile = codebase.get_file("testdir/__init__.py")
        file3: SourceFile = codebase.get_file("test3.py")

        symb = file1.get_symbol("TEST_CONST")
        test = file2.get_symbol("test")
        bar = file2.get_symbol("bar")
        mid_import = file2.get_import("testdir.test1")
        test3 = file3.get_symbol("test3")

        assert len(symb.usages) == 2
        assert symb.symbol_usages == [test, test3]
        assert mid_import.symbol_usages == [test, bar, test3]


def test_import_resolution_init_deep_nested_wildcards(tmpdir: str) -> None:
    """Tests that chaining wildcard imports resolves properly"""
    # language=python

    files = {
        "test/nest/nest2/test1.py": """test_const=5
           test_not_used=2
           test_used_parent=5
           """,
        "test/nest/nest2/__init__.py": """from .test1 import *
           t1=test_used_parent
           """,
        "test/nest/__init__.py": """from .nest2 import *""",
        "test/__init__.py": """from .nest import *""",
        "main.py": """
            from test import *
            main_test=test_const
           """,
    }
    with get_codebase_session(tmpdir=tmpdir, files=files) as codebase:
        deepest_layer: SourceFile = codebase.get_file("test/nest/nest2/test1.py")
        main: SourceFile = codebase.get_file("main.py")
        parent_file: SourceFile = codebase.get_file("test/nest/nest2/__init__.py")

        main_test = main.get_symbol("main_test")
        t1 = parent_file.get_symbol("t1")
        test_const = deepest_layer.get_symbol("test_const")
        test_not_used = deepest_layer.get_symbol("test_not_used")
        test_used_parent = deepest_layer.get_symbol("test_used_parent")

        assert len(test_const.usages) == 1
        assert test_const.usages[0].usage_symbol == main_test
        assert len(test_not_used.usages) == 0
        assert len(test_used_parent.usages) == 1
        assert test_used_parent.usages[0].usage_symbol == t1


def test_import_resolution_chaining_many_wildcards(tmpdir: str) -> None:
    """Tests that chaining wildcard imports resolves properly"""
    # language=python

    files = {
        "test1.py": """
           test_const=5
           test_not_used=2
           test_used_parent=5
           """,
        "test2.py": """from test1 import *
           t1=test_used_parent
           """,
        "test3.py": """from test2 import *""",
        "test4.py": """from test3 import *""",
        "main.py": """
            from test4 import *
            main_test=test_const
           """,
    }
    with get_codebase_session(tmpdir=tmpdir, files=files) as codebase:
        furthest_layer: SourceFile = codebase.get_file("test1.py")
        main: SourceFile = codebase.get_file("main.py")
        parent_file: SourceFile = codebase.get_file("test2.py")

        main_test = main.get_symbol("main_test")
        t1 = parent_file.get_symbol("t1")
        test_const = furthest_layer.get_symbol("test_const")
        test_not_used = furthest_layer.get_symbol("test_not_used")
        test_used_parent = furthest_layer.get_symbol("test_used_parent")

        assert len(test_const.usages) == 1
        assert test_const.usages[0].usage_symbol == main_test
        assert len(test_not_used.usages) == 0
        assert len(test_used_parent.usages) == 1
        assert test_used_parent.usages[0].usage_symbol == t1


def test_import_resolution_init_deep_nested_wildcards_named(tmpdir: str) -> None:
    """Tests that chaining wildcard imports resolves properly"""
    # language=python

    files = {
        "test/nest/nest2/test1.py": """test_const=5
           test_not_used=2
           test_used_parent=5
           """,
        "test/nest/nest2/__init__.py": """from .test1 import *
           t1=test_used_parent
           """,
        "test/nest/__init__.py": """from .nest2 import *""",
        "test/__init__.py": """from .nest import *""",
        "main.py": """
            from test import test_const
            main_test=test_const
           """,
    }
    with get_codebase_session(tmpdir=tmpdir, files=files) as codebase:
        deepest_layer: SourceFile = codebase.get_file("test/nest/nest2/test1.py")
        main: SourceFile = codebase.get_file("main.py")
        parent_file: SourceFile = codebase.get_file("test/nest/nest2/__init__.py")
        test_nest: SourceFile = codebase.get_file("test/__init__.py")

        main_test = main.get_symbol("main_test")
        t1 = parent_file.get_symbol("t1")
        test_const = deepest_layer.get_symbol("test_const")
        test_not_used = deepest_layer.get_symbol("test_not_used")
        test_used_parent = deepest_layer.get_symbol("test_used_parent")

        test_const_imp = main.get_import("test_const")

        assert len(test_const.usages) == 2
        assert test_const.usages[0].usage_symbol == main_test
        assert test_const.usages[1].usage_symbol == test_const_imp

        assert len(test_not_used.usages) == 0
        assert len(test_used_parent.usages) == 1
        assert test_used_parent.usages[0].usage_symbol == t1


def test_import_resolution_circular(tmpdir: str) -> None:
    """Tests function.usages returns usages from file imports"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a.py": """
from b import *
def a_sym():
    pass
""",
            "b.py": """
from c import *
def b_sym():
    pass

""",
            "c.py": """
from a import *
def c_sym():
    pass

        """,
        },
    ) as codebase:
        a_file: SourceFile = codebase.get_file("a.py")
        b_file: SourceFile = codebase.get_file("b.py")
        c_file: SourceFile = codebase.get_file("c.py")
        assert "b_sym" in a_file.valid_symbol_names
        assert "c_sym" in a_file.valid_symbol_names
        assert "a_sym" in b_file.valid_symbol_names
        assert "c_sym" in b_file.valid_symbol_names
        assert "a_sym" in c_file.valid_symbol_names
        assert "b_sym" in c_file.valid_symbol_names.keys()


def test_import_resolution_nested_module(tmpdir: str) -> None:
    """Tests import resolution works with nested module imports"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a/b/c.py": """
def d():
    pass
""",
            "consumer.py": """
from a import b

b.c.d()
""",
        },
    ) as codebase:
        consumer_file: SourceFile = codebase.get_file("consumer.py")
        c_file: SourceFile = codebase.get_file("a/b/c.py")

        # Verify import resolution
        assert len(consumer_file.imports) == 1

        # Verify function call resolution
        d_func = c_file.get_function("d")
        call_sites = d_func.call_sites
        assert len(call_sites) == 1
        assert call_sites[0].file == consumer_file


def test_import_resolution_nested_module_init(tmpdir: str) -> None:
    """Tests import resolution works with nested module imports"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a/b/c.py": """
def d():
    pass
""",
            "a/b/__init__.py": """""",
            "consumer.py": """
from a import b

b.c.d()
""",
        },
    ) as codebase:
        consumer_file: SourceFile = codebase.get_file("consumer.py")
        c_file: SourceFile = codebase.get_file("a/b/c.py")

        # Verify import resolution
        assert len(consumer_file.imports) == 1

        # Verify function call resolution
        d_func = c_file.get_function("d")
        call_sites = d_func.call_sites
        assert len(call_sites) == 1
        assert call_sites[0].file == consumer_file


def test_import_resolution_module_attribute_access(tmpdir: str) -> None:
    """Tests that function usages are detected when accessed via module attribute notation"""
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "a/b/module.py": """
def some_func():
    pass
""",
            "consumer.py": """
from a.b import module

module.some_func()
""",
        },
    ) as codebase:
        module_file: SourceFile = codebase.get_file("a/b/module.py")
        consumer_file: SourceFile = codebase.get_file("consumer.py")

        # Verify function call resolution
        some_func = module_file.get_function("some_func")
        call_sites = some_func.call_sites
        assert len(call_sites) == 1
        assert call_sites[0].file == consumer_file

        # Verify usages are detected
        assert len(some_func.usages) > 0
        assert len(some_func.symbol_usages) > 0


def test_import_wildcard_preserves_import_resolution(tmpdir: str) -> None:
    """Tests importing from a file that contains a wildcard import doesn't break further resolution.
    This could occur depending on to_resolve ordering, if the outer file is processed first _wildcards will not be filled in time.
    """
    # language=python
    with get_codebase_session(
        tmpdir,
        files={
            "testdir/sub/file.py": """
                test_const=5
                b=2
            """,
            "testdir/file.py": """
            from testdir.sub.file import *
            c=b
            """,
            "file.py": """
            from testdir.file import test_const
            test = test_const
            """,
        },
    ) as codebase:
        mainfile: SourceFile = codebase.get_file("file.py")

        assert len(mainfile.ctx.edges) == 10


def test_import_resolution_init_wildcard_no_dupe(tmpdir: str) -> None:
    """Tests that named import from a file with wildcard resolves properly and doesn't
    result in duplicate usages
    """
    # language=python
    content1 = """TEST_CONST=2
    foo=9
    """
    content2 = """from testdir.test1 import *
    bar=foo
    test=TEST_CONST"""
    content3 = """from testdir import TEST_CONST
    test3=TEST_CONST"""
    content4 = """from testdir import  foo
    test4=foo"""
    with get_codebase_session(tmpdir=tmpdir, files={"testdir/test1.py": content1, "testdir/__init__.py": content2, "test3.py": content3, "test4.py": content4}) as codebase:
        file1: SourceFile = codebase.get_file("testdir/test1.py")
        file2: SourceFile = codebase.get_file("testdir/__init__.py")
        file3: SourceFile = codebase.get_file("test3.py")

        symb = file1.get_symbol("TEST_CONST")
        test = file2.get_symbol("test")
        test3 = file3.get_symbol("test3")
        test3_import = file3.get_import("TEST_CONST")

        assert len(symb.usages) == 3
        assert symb.symbol_usages == [test, test3, test3_import]


def test_import_resolution_init_wildcard_chainging_deep(tmpdir: str) -> None:
    """Tests that named import from a file with wildcard resolves properly and doesn't
    result in duplicate usages
    """
    # language=python
    content1 = """TEST_CONST=2
    """
    content2 = """from .file1 import *"""
    content3 = """from .dir import *"""
    content4 = """from .dir import  TEST_CONST
    test1=TEST_CONST"""
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "dir/dir/dir/dir/file1.py": content1,
            "dir/dir/dir/dir/__init__.py": content2,
            "dir/dir/dir/__init__.py": content3,
            "dir/dir/__init__.py": content3,
            "dir/__init__.py": content3,
            "file2.py": content4,
        },
    ) as codebase:
        file1: SourceFile = codebase.get_file("dir/dir/dir/dir/file1.py")
        file2: SourceFile = codebase.get_file("file2.py")

        symb = file1.get_symbol("TEST_CONST")
        test1 = file2.get_symbol("test1")
        imp = file2.get_import("TEST_CONST")

        assert len(symb.usages) == 2
        assert symb.symbol_usages == [test1, imp]


def test_import_resolution_paths_init(tmpdir: str) -> None:
    cfg = TestFlags.model_copy()
    cfg.debug = False  ##Disable to ignore binary expression edge duplicate
    cfg.import_resolution_paths = ["package"]

    # language=python
    content1 = """
    COMMON_AVAILABLE_STREAMS = [
        1,
        2,
        3,
        4,
        5,
        6,
    ]

    PLAN_MODEL_AVAILABLE_STREAMS = COMMON_AVAILABLE_STREAMS + [
        4,
        2
    ]
"""
    content2 = """
        from main.dir.dir2 import PLAN_MODEL_AVAILABLE_STREAMS
        def do_smth():
            foo=PLAN_MODEL_AVAILABLE_STREAMS
            print(foo)

        do_smth()
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        config=cfg,
        files={
            "package/main/dir/dir2/file1.py": "bar=2",
            "package/main/dir/dir2/__init__.py": content1,
            "package/main/dir/__init__.py": content2,
            "package/main/__init__.py": "",
            "start.py": """from main.dir.dir2.file1 import bar
            print(bar)
            """,
        },
    ) as codebase:
        file1: SourceFile = codebase.get_file("package/main/dir/dir2/__init__.py")
        p_m = file1.get_symbol("PLAN_MODEL_AVAILABLE_STREAMS")
        file2: SourceFile = codebase.get_file("package/main/dir/__init__.py")
        dosmth = file2.get_symbol("do_smth")
        import_pm = file2.get_import("PLAN_MODEL_AVAILABLE_STREAMS")

        assert len(p_m.usages) == 3
        assert p_m.symbol_usages == [dosmth, import_pm]
        assert len(file1.symbols) != 1
