"""Constants for the Hargassner HSV integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "hargassner_hsv"

CONF_SOURCES: Final = "sources"
DEFAULT_PORT: Final = 8080

# The Pi API contract this integration speaks (api/ha_v1.schema.json).
# Minor versions only add fields, so any 1.x is fine.
API_MAJOR: Final = 1

STATE_INTERVAL: Final = timedelta(seconds=15)
TOTALS_INTERVAL: Final = timedelta(minutes=5)
TIMEOUT_FAST: Final = 10
# /totals needs about 2.5 s on the Pi, more right after a restart.
TIMEOUT_TOTALS: Final = 30

# Devices of one config entry. "logger" is the Pi itself and acts as the hub.
SOURCES: Final = ("boiler", "solar", "grid", "dairy_room", "weather", "logger")

BOILER_STATES: Final = [
    "off", "refill_soon", "refill", "grate_check", "start",
    "fuel_feed_ignition_check", "ignition", "full_load", "ember_hold",
    "deashing_prepare", "burnout", "deashing", "cleaning_start", "cleaning",
    "cleaning_end", "unknown",
]
DHW_MODES: Final = ["loading", "residual_heat", "off", "other"]
HK1_MODES: Final = ["heating", "residual_heat", "summer_off", "setback", "off", "other"]
