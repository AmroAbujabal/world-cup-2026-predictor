# backend/services/football_data.py
"""football-data.org API client (async + sync) for WC 2026 data."""

import os
import httpx

FDORG_BASE = "https://api.football-data.org/v4"

# football-data.org name → our canonical name (matches results.csv / wc2026.js)
NAME_MAP = {
    "Côte d'Ivoire": "Ivory Coast",
    "United States": "USA",
    "Republic of Korea": "South Korea",
    "IR Iran": "Iran",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Congo DR": "DR Congo",
    "Democratic Republic of Congo": "DR Congo",
    "Czechia": "Czech Republic",
    "Curaçao": "Curacao",
    "Cape Verde Islands": "Cape Verde",
    "Cabo Verde": "Cape Verde",
}


def normalize(name: str) -> str:
    return NAME_MAP.get(name, name)


def _headers() -> dict:
    key = os.getenv("FOOTBALL_DATA_API_KEY", "")
    return {"X-Auth-Token": key}


def sync_get_wc_matches(stage: str | None = None) -> list[dict]:
    """Synchronous — for use in seed scripts."""
    params: dict = {"season": "2026"}
    if stage:
        params["stage"] = stage
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{FDORG_BASE}/competitions/WC/matches",
            params=params,
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()["matches"]


async def get_wc_matches(stage: str | None = None) -> list[dict]:
    """Async — for use in the poller background task."""
    params: dict = {"season": "2026"}
    if stage:
        params["stage"] = stage
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{FDORG_BASE}/competitions/WC/matches",
            params=params,
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()["matches"]
