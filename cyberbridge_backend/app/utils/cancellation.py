import asyncio
import logging
from typing import Dict, Any, Optional

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# Registry of active LLM tasks keyed by user ID.
# Stores the asyncio.Task running the LLM call so it can be cancelled.
_active_tasks: Dict[str, asyncio.Task] = {}


def register_task(user_id: str, task: asyncio.Task) -> None:
    """Register the asyncio Task running the LLM call for the given user."""
    logger.info(f"Registered LLM task for user {user_id}")
    _active_tasks[user_id] = task


async def trigger_cancel(user_id: str) -> bool:
    """Cancel the asyncio Task running the LLM call for the given user.

    Cancelling the task causes httpx to close its connection to llama.cpp,
    which makes llama.cpp stop generating immediately.
    """
    logger.info(f"trigger_cancel called for user {user_id}, active_tasks keys: {list(_active_tasks.keys())}")
    task = _active_tasks.pop(user_id, None)
    if task and not task.done():
        logger.info(f"Cancelling LLM task for user {user_id}")
        task.cancel()
        return True
    return False


def unregister_task(user_id: str):
    """Remove the task reference after the LLM call completes."""
    _active_tasks.pop(user_id, None)


async def run_with_disconnect_check(request: Request, coro, poll_interval: float = 0.5):
    """Race a coroutine against client disconnect polling.

    Used by the suggestions controller to cancel LLM calls when the
    browser navigates away or the user aborts the fetch.
    """
    task = asyncio.ensure_future(coro)
    try:
        while not task.done():
            if await request.is_disconnected():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                raise HTTPException(status_code=499, detail="Client disconnected")
            await asyncio.sleep(poll_interval)
        return task.result()
    except asyncio.CancelledError:
        task.cancel()
        raise
