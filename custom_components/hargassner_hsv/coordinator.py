"""Data update coordinators for the Hargassner HSV integration."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HargassnerApi, HargassnerApiError, HargassnerAuthError

_LOGGER = logging.getLogger(__name__)


class HargassnerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls one endpoint of the Pi API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        name: str,
        fetch: Callable[[], Awaitable[dict[str, Any]]],
        interval: timedelta,
    ) -> None:
        super().__init__(
            hass, _LOGGER, config_entry=entry, name=name, update_interval=interval
        )
        self._fetch = fetch

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self._fetch()
        except HargassnerAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except HargassnerApiError as err:
            raise UpdateFailed(str(err)) from err


@dataclass
class HargassnerRuntime:
    """Everything a config entry needs at runtime."""

    api: HargassnerApi
    info: dict[str, Any]
    state: HargassnerCoordinator
    totals: HargassnerCoordinator
    hub_device_id: str | None = None
