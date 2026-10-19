"""Sensors for the Hargassner HSV integration.

Values that the controller does not measure but the Pi calculates (heat,
pellets, efficiency, solar heat) carry ``origin: calculated`` and the
assumptions they depend on as attributes - the same disclosure as on the
Pi's own web page.

Statistics rules (see README, "Statistics done right"):
* Device meters (grid 1.8.0/2.8.0, cleaned solar total) are TOTAL_INCREASING.
* Calculated grand totals (heat, pellets) are TOTAL: they are recalculated
  from the whole history and drop when an assumption is corrected.
* Daily values are TOTAL with last_reset at local midnight.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfInformation,
    UnitOfIrradiance,
    UnitOfMass,
    UnitOfPower,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfReactivePower,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from . import HargassnerConfigEntry
from .const import BOILER_STATES, CONF_SOURCES, DHW_MODES, HK1_MODES, SOURCES
from .entity import HargassnerEntity, HargassnerEntityDescription

M = SensorStateClass.MEASUREMENT
T = SensorStateClass.TOTAL
TI = SensorStateClass.TOTAL_INCREASING
DIAG = EntityCategory.DIAGNOSTIC
C = UnitOfTemperature.CELSIUS


@dataclass(frozen=True, kw_only=True)
class HargassnerSensorDescription(HargassnerEntityDescription, SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], StateType]
    # last_reset = local midnight from /totals
    daily: bool = False
    # extra attributes, computed from (data, info)
    attrs_fn: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None


def v(section: str, key: str) -> Callable[[dict[str, Any]], StateType]:
    return lambda d: (d.get(section) or {}).get(key)


def boiler_calc(_d: dict[str, Any], info: dict[str, Any]) -> dict[str, Any]:
    a = info.get("assumptions") or {}
    return {
        "origin": "calculated",
        "nominal_power_kw": a.get("nominal_power_kw"),
        "heating_value_kwh_kg": a.get("heating_value_kwh_kg"),
        "boiler_efficiency": a.get("boiler_efficiency"),
        "cycle_s": a.get("cycle_s"),
        "note": "Calculated from boiler output %; ignition fuel is not included.",
    }


def efficiency_calc(_d: dict[str, Any], _info: dict[str, Any]) -> dict[str, Any]:
    return {
        "origin": "calculated",
        "note": "Combustion efficiency (Siegert, flue gas loss only), states 6/7/9.",
    }


def solar_calc(_d: dict[str, Any], info: dict[str, Any]) -> dict[str, Any]:
    a = info.get("assumptions") or {}
    return {
        "origin": "calculated",
        "flow_assumption_l_h": a.get("solar_flow_l_h"),
        "antifreeze_factor": a.get("solar_antifreeze_factor"),
        "scale_mismatch_factor": a.get("solar_scale_mismatch_factor"),
        "correction_factor": a.get("solar_correction_factor"),
        "note": (
            "Absolute values depend on the fixed flow rate set in the ESR21; "
            "trends and day-to-day comparisons are reliable. Current power and "
            "the energy meter differ by the scale mismatch factor (unresolved)."
        ),
    }


def household_note(_d: dict[str, Any], _info: dict[str, Any]) -> dict[str, Any]:
    return {
        "origin": "calculated",
        "note": "Whole household, pure full-load minutes minus pure off minutes.",
    }


def age(source: str) -> Callable[[dict[str, Any]], StateType]:
    return lambda d: ((d.get("sources") or {}).get(source) or {}).get("age_s")


def temp(key: str, field: str, device: str, source: str, **kw: Any) -> HargassnerSensorDescription:
    return HargassnerSensorDescription(
        key=key, translation_key=key, device=device, source=source,
        device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=C,
        state_class=M, suggested_display_precision=1,
        value_fn=v(source, field), **kw,
    )


def pct(key: str, field: str, device: str, source: str, **kw: Any) -> HargassnerSensorDescription:
    return HargassnerSensorDescription(
        key=key, translation_key=key, device=device, source=source,
        native_unit_of_measurement=PERCENTAGE, state_class=M,
        suggested_display_precision=kw.pop("precision", 0),
        value_fn=v(source, field), **kw,
    )


BOILER: tuple[HargassnerSensorDescription, ...] = (
    HargassnerSensorDescription(
        key="boiler_state", translation_key="boiler_state", device="boiler", source="boiler",
        device_class=SensorDeviceClass.ENUM, options=BOILER_STATES,
        value_fn=v("boiler", "state"),
        attrs_fn=lambda d, _i: {"state_code": (d.get("boiler") or {}).get("state_code")},
    ),
    temp("boiler_temp", "boiler_temp_c", "boiler", "boiler"),
    temp("boiler_target", "boiler_target_c", "boiler", "boiler"),
    temp("flue_gas_temp", "flue_gas_temp_c", "boiler", "boiler"),
    pct("o2", "o2_percent", "boiler", "boiler", precision=1),
    pct("o2_target", "o2_target_percent", "boiler", "boiler", precision=1,
        entity_registry_enabled_default=False),
    pct("output", "output_percent", "boiler", "boiler"),
    HargassnerSensorDescription(
        key="boiler_heat_power", translation_key="boiler_heat_power", device="boiler",
        source="boiler", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT, state_class=M,
        suggested_display_precision=1, value_fn=v("boiler", "heat_power_kw"),
        attrs_fn=boiler_calc,
    ),
    pct("feed_rate", "feed_rate_percent", "boiler", "boiler"),
    HargassnerSensorDescription(
        key="draft_fan", translation_key="draft_fan", device="boiler", source="boiler",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE, state_class=M,
        suggested_display_precision=0, value_fn=v("boiler", "draft_fan_rpm"),
    ),
    pct("draft_fan_target", "draft_fan_target_percent", "boiler", "boiler",
        entity_registry_enabled_default=False),
    pct("air", "air_percent", "boiler", "boiler", entity_registry_enabled_default=False),
    pct("air_corrected", "air_corrected_percent", "boiler", "boiler",
        entity_registry_enabled_default=False),
    temp("dhw_temp", "dhw_temp_c", "boiler", "boiler"),
    temp("hk1_flow_temp", "hk1_flow_temp_c", "boiler", "boiler"),
    temp("hk1_flow_target", "hk1_flow_target_c", "boiler", "boiler"),
    temp("room_temp", "room_temp_c", "boiler", "boiler"),
    temp("outdoor_temp", "outdoor_temp_c", "boiler", "boiler"),
    temp("outdoor_avg", "outdoor_avg_c", "boiler", "boiler",
         entity_registry_enabled_default=False),
    HargassnerSensorDescription(
        key="combustion_efficiency", translation_key="combustion_efficiency",
        device="boiler", source="boiler", native_unit_of_measurement=PERCENTAGE,
        state_class=M, suggested_display_precision=1,
        value_fn=v("boiler", "efficiency_percent"), attrs_fn=efficiency_calc,
    ),
    HargassnerSensorDescription(
        key="dhw_mode", translation_key="dhw_mode", device="boiler", source="boiler",
        device_class=SensorDeviceClass.ENUM, options=DHW_MODES,
        value_fn=v("boiler", "dhw_mode"),
        attrs_fn=lambda d, _i: {"since": (d.get("boiler") or {}).get("dhw_mode_since"),
                                "origin": "controller_message"},
    ),
    HargassnerSensorDescription(
        key="hk1_mode", translation_key="hk1_mode", device="boiler", source="boiler",
        device_class=SensorDeviceClass.ENUM, options=HK1_MODES,
        value_fn=v("boiler", "hk1_mode"),
        attrs_fn=lambda d, _i: {"since": (d.get("boiler") or {}).get("hk1_mode_since"),
                                "origin": "controller_message"},
    ),
    HargassnerSensorDescription(
        key="feed_screw_current", translation_key="feed_screw_current", device="boiler",
        source="boiler", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, state_class=M,
        entity_category=DIAG, entity_registry_enabled_default=False,
        value_fn=v("boiler", "feed_screw_current_ma"),
    ),
    HargassnerSensorDescription(
        key="room_discharge_current", translation_key="room_discharge_current",
        device="boiler", source="boiler", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, state_class=M,
        entity_category=DIAG, entity_registry_enabled_default=False,
        value_fn=v("boiler", "room_discharge_current_a"),
    ),
    HargassnerSensorDescription(
        key="grate_current", translation_key="grate_current", device="boiler",
        source="boiler", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, state_class=M,
        entity_category=DIAG, entity_registry_enabled_default=False,
        value_fn=v("boiler", "grate_current_ma"),
    ),
    HargassnerSensorDescription(
        key="cleaning_current", translation_key="cleaning_current", device="boiler",
        source="boiler", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, state_class=M,
        entity_category=DIAG, entity_registry_enabled_default=False,
        value_fn=v("boiler", "cleaning_current_a"),
    ),
    *(
        HargassnerSensorDescription(
            key=f"counter_{x}", translation_key=f"counter_{x}", device="boiler",
            source="boiler", entity_category=DIAG, entity_registry_enabled_default=False,
            value_fn=v("boiler", f"counter_{x}"),
        )
        for x in ("a", "b", "c")
    ),
    # --- from /totals ---
    HargassnerSensorDescription(
        key="boiler_heat_today", translation_key="boiler_heat_today", device="boiler",
        coordinator="totals", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=T, daily=True,
        suggested_display_precision=1, value_fn=v("boiler", "heat_today_kwh"),
        attrs_fn=boiler_calc,
    ),
    HargassnerSensorDescription(
        key="pellets_today", translation_key="pellets_today", device="boiler",
        coordinator="totals", device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS, state_class=T, daily=True,
        suggested_display_precision=1, value_fn=v("boiler", "pellets_today_kg"),
        attrs_fn=boiler_calc,
    ),
    HargassnerSensorDescription(
        key="burner_starts_today", translation_key="burner_starts_today", device="boiler",
        coordinator="totals", state_class=T, daily=True,
        value_fn=v("boiler", "starts_today"),
    ),
    HargassnerSensorDescription(
        key="burn_time_today", translation_key="burn_time_today", device="boiler",
        coordinator="totals", device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES, state_class=T, daily=True,
        suggested_display_precision=0, value_fn=v("boiler", "burn_minutes_today"),
    ),
    HargassnerSensorDescription(
        key="active_time_today", translation_key="active_time_today", device="boiler",
        coordinator="totals", device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES, state_class=T, daily=True,
        suggested_display_precision=0, entity_registry_enabled_default=False,
        value_fn=v("boiler", "active_minutes_today"),
    ),
    HargassnerSensorDescription(
        key="boiler_heat_total", translation_key="boiler_heat_total", device="boiler",
        coordinator="totals", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=T,
        suggested_display_precision=0, value_fn=v("boiler", "heat_total_kwh"),
        attrs_fn=boiler_calc,
    ),
    HargassnerSensorDescription(
        key="pellets_total", translation_key="pellets_total", device="boiler",
        coordinator="totals", device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS, state_class=T,
        suggested_display_precision=0, value_fn=v("boiler", "pellets_total_kg"),
        attrs_fn=boiler_calc,
    ),
    HargassnerSensorDescription(
        key="burner_starts_total", translation_key="burner_starts_total", device="boiler",
        coordinator="totals", state_class=T, value_fn=v("boiler", "starts_total"),
    ),
    HargassnerSensorDescription(
        key="burn_time_total", translation_key="burn_time_total", device="boiler",
        coordinator="totals", device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS, state_class=T,
        suggested_display_precision=0, value_fn=v("boiler", "burn_minutes_total"),
    ),
)

SOLAR: tuple[HargassnerSensorDescription, ...] = (
    temp("collector_temp", "collector_temp_c", "solar", "solar"),
    temp("tank_bottom_temp", "tank_bottom_temp_c", "solar", "solar"),
    HargassnerSensorDescription(
        key="solar_spread", translation_key="solar_spread", device="solar", source="solar",
        native_unit_of_measurement=UnitOfTemperature.KELVIN, state_class=M,
        suggested_display_precision=1, value_fn=v("solar", "spread_k"),
    ),
    HargassnerSensorDescription(
        key="solar_heat_power", translation_key="solar_heat_power", device="solar",
        source="solar", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT, state_class=M,
        suggested_display_precision=1, value_fn=v("solar", "power_kw"),
        attrs_fn=solar_calc,
    ),
    HargassnerSensorDescription(
        key="solar_flow", translation_key="solar_flow", device="solar", source="solar",
        native_unit_of_measurement="L/h", state_class=M, entity_category=DIAG,
        entity_registry_enabled_default=False, value_fn=v("solar", "flow_l_h"),
    ),
    HargassnerSensorDescription(
        # Raw ESR21 meter, no statistics: it contains glitches (1025, 2050 MWh).
        key="solar_meter_raw", translation_key="solar_meter_raw", device="solar",
        source="solar", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.MEGA_WATT_HOUR,
        suggested_display_precision=4, entity_category=DIAG,
        entity_registry_enabled_default=False, value_fn=v("solar", "meter_mwh"),
    ),
    HargassnerSensorDescription(
        key="solar_heat_total", translation_key="solar_heat_total", device="solar",
        coordinator="totals", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=TI,
        suggested_display_precision=1, value_fn=v("solar", "energy_total_kwh"),
        attrs_fn=lambda d, i: {**solar_calc(d, i),
                               "since": (d.get("solar") or {}).get("energy_total_since")},
    ),
    HargassnerSensorDescription(
        key="solar_heat_today", translation_key="solar_heat_today", device="solar",
        coordinator="totals", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=T, daily=True,
        suggested_display_precision=1, value_fn=v("solar", "energy_today_kwh"),
        attrs_fn=solar_calc,
    ),
    HargassnerSensorDescription(
        key="solar_pump_hours_today", translation_key="solar_pump_hours_today",
        device="solar", coordinator="totals", device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS, state_class=T, daily=True,
        suggested_display_precision=1, value_fn=v("solar", "pump_hours_today"),
    ),
    HargassnerSensorDescription(
        key="solar_pump_starts_today", translation_key="solar_pump_starts_today",
        device="solar", coordinator="totals", state_class=T, daily=True,
        value_fn=v("solar", "pump_starts_today"),
    ),
)


def power(key: str, field: str, device: str, source: str, **kw: Any) -> HargassnerSensorDescription:
    return HargassnerSensorDescription(
        key=key, translation_key=key, device=device, source=source,
        device_class=SensorDeviceClass.POWER, native_unit_of_measurement=UnitOfPower.WATT,
        state_class=M, suggested_display_precision=0, value_fn=v(source, field), **kw,
    )


def meter(key: str, field: str, device: str, source: str, **kw: Any) -> HargassnerSensorDescription:
    return HargassnerSensorDescription(
        key=key, translation_key=key, device=device, source=source,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=TI,
        suggested_display_precision=3, value_fn=v(source, field), **kw,
    )


GRID: tuple[HargassnerSensorDescription, ...] = (
    power("grid_import_power", "import_power_w", "grid", "grid"),
    power("grid_export_power", "export_power_w", "grid", "grid"),
    power("grid_net_power", "net_power_w", "grid", "grid"),
    meter("grid_import_energy", "import_kwh", "grid", "grid"),
    meter("grid_export_energy", "export_kwh", "grid", "grid"),
    *(
        HargassnerSensorDescription(
            key=key, translation_key=key, device="grid", source="grid",
            device_class=SensorDeviceClass.REACTIVE_POWER,
            native_unit_of_measurement=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
            state_class=M, entity_registry_enabled_default=False, value_fn=v("grid", field),
        )
        for key, field in (("grid_reactive_import_power", "reactive_import_var"),
                           ("grid_reactive_export_power", "reactive_export_var"))
    ),
    *(
        HargassnerSensorDescription(
            key=key, translation_key=key, device="grid", source="grid",
            native_unit_of_measurement="kvarh", state_class=TI,
            entity_registry_enabled_default=False, value_fn=v("grid", field),
        )
        for key, field in (("grid_reactive_import_energy", "reactive_import_kvarh"),
                           ("grid_reactive_export_energy", "reactive_export_kvarh"))
    ),
    meter("grid_collection_energy", "collection_kwh", "grid", "grid",
          entity_registry_enabled_default=False),
    HargassnerSensorDescription(
        key="grid_import_today", translation_key="grid_import_today", device="grid",
        coordinator="totals", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=T, daily=True,
        suggested_display_precision=2, value_fn=v("grid", "import_today_kwh"),
    ),
    HargassnerSensorDescription(
        key="grid_export_today", translation_key="grid_export_today", device="grid",
        coordinator="totals", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=T, daily=True,
        suggested_display_precision=2, value_fn=v("grid", "export_today_kwh"),
    ),
    HargassnerSensorDescription(
        key="base_load", translation_key="base_load", device="grid", coordinator="totals",
        device_class=SensorDeviceClass.POWER, native_unit_of_measurement=UnitOfPower.WATT,
        state_class=M, suggested_display_precision=0, value_fn=v("grid", "base_load_w"),
        attrs_fn=lambda _d, _i: {"note": "Lowest net import 00-05 h, last 24 h."},
    ),
    HargassnerSensorDescription(
        key="extra_load_burning", translation_key="extra_load_burning", device="grid",
        coordinator="totals", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT, state_class=M,
        suggested_display_precision=0, value_fn=v("grid", "extra_load_burning_w"),
        attrs_fn=household_note,
    ),
)

DAIRY: tuple[HargassnerSensorDescription, ...] = (
    power("dairy_power", "power_w", "dairy_room", "dairy_room"),
    meter("dairy_energy", "energy_kwh", "dairy_room", "dairy_room"),
    HargassnerSensorDescription(
        key="dairy_energy_today", translation_key="dairy_energy_today",
        device="dairy_room", coordinator="totals", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=T, daily=True,
        suggested_display_precision=2, value_fn=v("dairy_room", "energy_today_kwh"),
    ),
)


def weather(key: str, field: str, **kw: Any) -> HargassnerSensorDescription:
    # HA has its own weather integrations; these are the values the Pi
    # calculates with, so they are disabled by default.
    return HargassnerSensorDescription(
        key=key, translation_key=key, device="weather", source="weather",
        state_class=M, entity_registry_enabled_default=False,
        value_fn=v("weather", field), **kw,
    )


WEATHER: tuple[HargassnerSensorDescription, ...] = (
    weather("weather_temperature", "temperature_c", device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=C),
    weather("weather_apparent_temperature", "apparent_temperature_c",
            device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=C),
    weather("weather_humidity", "humidity_percent", device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE),
    weather("weather_precipitation", "precipitation_mm",
            device_class=SensorDeviceClass.PRECIPITATION,
            native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS),
    weather("weather_cloud_cover", "cloud_cover_percent", native_unit_of_measurement=PERCENTAGE),
    weather("weather_pressure", "pressure_hpa", device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
            native_unit_of_measurement=UnitOfPressure.HPA),
    weather("weather_wind", "wind_kmh", device_class=SensorDeviceClass.WIND_SPEED,
            native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR),
    weather("weather_gusts", "gusts_kmh", device_class=SensorDeviceClass.WIND_SPEED,
            native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR),
    weather("weather_wind_direction", "wind_direction_deg", native_unit_of_measurement=DEGREE),
    weather("weather_radiation", "radiation_w_m2", device_class=SensorDeviceClass.IRRADIANCE,
            native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER),
    HargassnerSensorDescription(
        key="weather_code", translation_key="weather_code", device="weather",
        source="weather", entity_registry_enabled_default=False,
        value_fn=v("weather", "weather_code"),
    ),
)

LOGGER: tuple[HargassnerSensorDescription, ...] = (
    *(
        HargassnerSensorDescription(
            key=f"age_{s}", translation_key=f"age_{s}", device="logger",
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS, state_class=M,
            suggested_display_precision=0, entity_category=DIAG,
            entity_registry_enabled_default=s in ("boiler", "solar", "grid"),
            value_fn=age(s),
        )
        for s in ("boiler", "solar", "grid", "dairy_room", "weather")
    ),
    HargassnerSensorDescription(
        key="database_size", translation_key="database_size", device="logger",
        coordinator="totals", device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES, state_class=M,
        suggested_display_precision=0, entity_category=DIAG,
        value_fn=v("system", "db_mb"),
    ),
    HargassnerSensorDescription(
        key="disk_free", translation_key="disk_free", device="logger",
        coordinator="totals", device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES, state_class=M,
        suggested_display_precision=1, entity_category=DIAG,
        value_fn=v("system", "free_gb"),
    ),
)

DESCRIPTIONS: tuple[HargassnerSensorDescription, ...] = (
    *BOILER, *SOLAR, *GRID, *DAIRY, *WEATHER, *LOGGER,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HargassnerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    selected = entry.options.get(CONF_SOURCES, list(SOURCES))
    runtime = entry.runtime_data
    async_add_entities(
        HargassnerSensor(runtime, d) for d in DESCRIPTIONS if d.device in selected
    )


class HargassnerSensor(HargassnerEntity, SensorEntity):
    entity_description: HargassnerSensorDescription

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def last_reset(self) -> datetime | None:
        if not self.entity_description.daily:
            return None
        start = self.coordinator.data.get("today_start")
        return dt_util.parse_datetime(start) if start else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fn = self.entity_description.attrs_fn
        return fn(self.coordinator.data, self.runtime.info) if fn else None
