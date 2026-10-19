"""Shared fixtures: real Pi API answers captured on 19.10.2026, id replaced."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hargassner_hsv.const import CONF_SOURCES, DOMAIN, SOURCES

FIXTURES = Path(__file__).parent / "fixtures"
HOST, PORT, TOKEN = "pi.example", 8080, "test-token-nicht-echt"
BASE = f"http://{HOST}:{PORT}/api/ha/v1"
INSTALLATION_ID = "00000000-0000-4000-8000-000000000001"


def load(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def entry_data() -> dict[str, Any]:
    return {CONF_HOST: HOST, CONF_PORT: PORT, CONF_TOKEN: TOKEN}


@pytest.fixture
def config_entry(entry_data) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=INSTALLATION_ID,
        data=entry_data,
        options={CONF_SOURCES: list(SOURCES)},
        title="Hargassner HSV 22",
    )


@pytest.fixture
def mock_pi(aioclient_mock):
    """The Pi answering all endpoints with the captured data."""

    def setup(state: dict | None = None, totals: dict | None = None, status: int = 200):
        aioclient_mock.clear_requests()
        for name, data in (("info", load("info")), ("state", state or load("state")),
                           ("totals", totals or load("totals")),
                           ("events", load("events_init"))):
            aioclient_mock.get(f"{BASE}/{name}", json=data, status=status)
        return aioclient_mock

    return setup
