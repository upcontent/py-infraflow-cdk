import asyncio
import functools
from typing import Callable


def as_async(func: Callable):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    return wrapper