
from collections.abc import Callable
from functools import cached_property
from typing import Generic, ParamSpec, TypeVar
import functools

from lazy_object_proxy import Proxy
from lazy_object_proxy.simple import make_proxy_method

from graph_sitter.compiled.utils import cached_property

# Handle optional lazy_object_proxy dependency
try:
    LAZY_PROXY_AVAILABLE = True
except ImportError:
    LAZY_PROXY_AVAILABLE = False
    # Create mock classes
    class Proxy:
        def __init__(self, factory):
            self.__factory__ = factory
        
        def __getattr__(self, name):
            obj = self.__factory__()
            return getattr(obj, name)
    
    def make_proxy_method(func):
        def wrapper(self):
            obj = self.__factory__()
            return func(obj)
        return wrapper

try:
except ModuleNotFoundError:

T = TypeVar("T")
P = ParamSpec("P")

class ProxyProperty(Proxy, Generic[P, T]):
    """Lazy proxy that can behave like a method or a property depending on how its used. The class it's proxying should not implement __call__"""

    __factory__: Callable[P, T]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self.__factory__(*args, **kwargs)

    __repr__ = make_proxy_method(repr)

def proxy_property(func: Callable[P, T]) -> cached_property[ProxyProperty[P, T]]:
    """Proxy a property so it behaves like a method and property simultaneously. When invoked as a property, results are cached and invalidated using uncache_all"""
    return cached_property(lambda obj: ProxyProperty(functools.partial(func, obj)))
