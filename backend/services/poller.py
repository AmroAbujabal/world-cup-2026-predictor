# backend/services/poller.py
"""Background polling task — fetches live WC results every 5 minutes."""

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

POLL_INTERVAL = 300  # 5 minutes
TOURNAMENT_START = datetime(2026, 6, 28, tzinfo=timezone.utc)
TOURNAMENT_END = datetime(2026, 7, 20, tzinfo=timezone.utc)


async def poll_loop():
    """Entry point: launched as asyncio background task on app startup.

    Every 5 minutes during the tournament, runs the self-driving sync so the whole
    bracket (teams, scores, statuses, probabilities, user points) stays current with
    the real results — no manual entry required.
    """
    await asyncio.sleep(15)  # let server fully start first
    logger.info("Poller started — syncing live results every 5 minutes during tournament")
    while True:
        now = datetime.now(timezone.utc)
        if TOURNAMENT_START <= now <= TOURNAMENT_END:
            try:
                # run_sync is blocking (HTTP + model) — keep it off the event loop
                summary = await asyncio.to_thread(_run_sync)
                if summary and (summary.get("scored") or summary.get("advanced")):
                    logger.info("Sync: %s", summary)
            except Exception as exc:
                logger.warning("Poller error: %s", exc)
        await asyncio.sleep(POLL_INTERVAL)


def _run_sync():
    from backend.services.sync_service import run_sync
    return run_sync()
