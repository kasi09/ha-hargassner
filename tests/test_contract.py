"""The captured test data must satisfy the shared contract with the Pi."""

import json
from pathlib import Path

import jsonschema
import pytest

from .conftest import load

SCHEMA = json.loads(
    (Path(__file__).parent.parent / "api" / "ha_v1.schema.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    ("fixture", "part"),
    [("info", "info"), ("state", "state"), ("totals", "totals"),
     ("events", "events"), ("events_init", "events")],
)
def test_fixture_matches_contract(fixture: str, part: str) -> None:
    validator = jsonschema.Draft202012Validator(
        {"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{part}"}
    )
    assert [e.message for e in validator.iter_errors(load(fixture))] == []
