# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2024 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

from typing import Awaitable, Callable
import asyncio
import logging


class BasicScheduler:
    background_loop: asyncio.Task | None
    tasks: set[asyncio.Task]
    log: logging.Logger

    def __init__(self, log: logging.Logger) -> None:
        self.log = log
        self.tasks = set()

    def _find_caller(self) -> str:
        try:
            file_name, line_number, function_name, _ = self.log.findCaller()
            return f"{function_name} at {file_name}:{line_number}"
        except ValueError:
            return "unknown function"

    def run_periodically(
        self,
        period: float | int,
        func: Callable[[], Awaitable],
        run_task_in_background: bool = False,
        catch_errors: bool = True,
    ) -> asyncio.Task:
        """
        Run a function periodically in the background.

        Args:
            period: The period in seconds between each call to the function.
            func: The function to run. No parameters will be provided,
                use :meth:`functools.partial` if you need to pass parameters.
            run_task_in_background: If ``True``, the function will be run in a background task.
                If ``False`` (the default), the loop will wait for the task to return before
                sleeping for the next period.
            catch_errors: Whether the scheduler should catch and log any errors.
                If ``False``, errors will be raised, and the caller must await the returned task
                to find errors. This parameter has no effect if ``run_task_in_background``
                is ``True``.

        Returns:
            The asyncio task object representing the background loop.
        """
        task = asyncio.create_task(
            self._call_periodically(
                period,
                func,
                caller=self._find_caller(),
                catch_errors=catch_errors,
                run_task_in_background=run_task_in_background,
            )
        )
        self._register_task(task)
        return task

    def run_later(
        self, delay: float | int, coro: Awaitable, catch_errors: bool = True
    ) -> asyncio.Task:
        """
        Run a coroutine after a delay.

        Examples:
            >>> self.sched.run_later(5, self.async_task(meow=True))

        Args:
            delay: The delay in seconds to await the coroutine after.
            coro: The coroutine to await.
            catch_errors: Whether the scheduler should catch and log any errors.
                If ``False``, errors will be raised, and the caller must await the returned task
                to find errors.

        Returns:
            The asyncio task object representing the scheduled task.
        """
        task = asyncio.create_task(
            self._call_with_delay(
                delay, coro, caller=self._find_caller(), catch_errors=catch_errors
            )
        )
        self._register_task(task)
        return task

    def _register_task(self, task: asyncio.Task) -> None:
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _call_periodically(
        self,
        period: float | int,
        func: Callable[[], Awaitable],
        caller: str,
        catch_errors: bool,
        run_task_in_background: bool,
    ) -> None:
        while True:
            try:
                await asyncio.sleep(period)
                if run_task_in_background:
                    self._register_task(
                        asyncio.create_task(self._call_periodically_background(func(), caller))
                    )
                else:
                    await func()
            except asyncio.CancelledError:
                raise
            except Exception:
                if catch_errors:
                    self.log.exception(f"Uncaught error in background loop (created in {caller})")
                else:
                    raise

    async def _call_periodically_background(self, coro: Awaitable, caller: str) -> None:
        try:
            await coro
        except asyncio.CancelledError:
            raise
        except Exception:
            self.log.exception(f"Uncaught error in background loop subtask (created in {caller})")

    async def _call_with_delay(
        self, delay: float | int, coro: Awaitable, caller: str, catch_errors: bool
    ) -> None:
        try:
            await asyncio.sleep(delay)
            await coro
        except asyncio.CancelledError:
            raise
        except Exception:
            if catch_errors:
                self.log.exception(f"Uncaught error in scheduled task (created in {caller})")
            else:
                raise

    def stop(self) -> None:
        """
        Stop all scheduled tasks and background loops.
        """
        for task in self.tasks:
            task.cancel(msg="Scheduler stopped")
