"""Client for the Pi API /api/ha/v1 (contract: api/ha_v1.schema.json)."""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import TIMEOUT_FAST, TIMEOUT_TOTALS


class HargassnerApiError(Exception):
    """The Pi could not be reached or answered with an error."""


class HargassnerAuthError(HargassnerApiError):
    """The token was rejected."""


class HargassnerApi:
    """Read-only access to the data logger on the Pi."""

    def __init__(
        self, session: aiohttp.ClientSession, host: str, port: int, token: str
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}/api/ha/v1"
        self._headers = {"Authorization": f"Bearer {token}"}

    async def _get(
        self, path: str, params: dict[str, Any] | None = None, timeout: int = TIMEOUT_FAST
    ) -> dict[str, Any]:
        try:
            async with self._session.get(
                f"{self._base}/{path}",
                headers=self._headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status == 401:
                    raise HargassnerAuthError("token rejected")
                if resp.status != 200:
                    raise HargassnerApiError(f"HTTP {resp.status} for {path}")
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise HargassnerApiError(f"{path}: {err}") from err

    async def info(self) -> dict[str, Any]:
        return await self._get("info")

    async def state(self) -> dict[str, Any]:
        return await self._get("state")

    async def totals(self) -> dict[str, Any]:
        return await self._get("totals", timeout=TIMEOUT_TOTALS)

    async def events(self, after_id: int | None = None) -> dict[str, Any]:
        params = {"after_id": after_id} if after_id is not None else None
        return await self._get("events", params=params)
