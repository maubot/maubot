from typing import Any, Awaitable, Callable, Generator


class FutureAwaitable:
    def __init__(self, func: Callable[[], Awaitable[None]]) -> None:
        self._func = func

    def __await__(self) -> Generator[Any, None, None]:
        return self._func().__await__()
