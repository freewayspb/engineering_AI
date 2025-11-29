import asyncio
import functools
from typing import Any, Callable, TypeVar

T = TypeVar("T")

try:
    to_thread = asyncio.to_thread  # Python 3.9+
except AttributeError:
    async def to_thread(func: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
        loop = asyncio.get_running_loop()
        bound = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, bound)

__all__ = ["to_thread"]
