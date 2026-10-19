# Hargassner HSV — Home Assistant integration

Brings a **Hargassner HSV 22** pellet boiler (Lambdatronic controller), its
**ESR21** solar thermal controller and the house **electricity meter** into
Home Assistant.

The data comes from a Raspberry Pi that records the boiler over its RS232
service port, the solar controller over the DL bus and the meter over an IR
reader. This integration only reads from that Pi's HTTP API (`/api/ha/v1`);
it never talks to the boiler itself. **It is read-only by design** — the
boiler only transmits, there is no way back.

> **Status: 0.1 — built for one specific installation.** The Pi side
> (`hsv-web` with `ha_api.py`) is not published yet. Without it this
> integration has nothing to connect to.

## What you get

| Device | Highlights |
|---|---|
| Boiler | state (15 states, translated), temperatures, O₂, output, **current heat (kW)**, hot water and heating circuit mode, heat and pellets today/total, burner starts |
| Solar thermal | collector, tank bottom, spread, pump, **current solar heat (kW)**, solar heat today/total |
| Electricity meter | import/export power and energy (1.8.0 / 2.8.0) — **ready for the Energy dashboard**, base load |
| Sub-meter | power and energy |
| Weather | the Open-Meteo values the Pi calculates with (disabled by default) |
| Data logger | service status, data age per source, database size |

### Calculated, not measured

The controller does not report heat or pellet consumption. These values are
calculated on the Pi and **marked as such** (`origin: calculated`, with the
assumptions as attributes):

* Boiler heat = output % × 22 kW. Ignition fuel is not included.
* Pellets = heat ÷ heating value ÷ efficiency (assumed, not measured).
* Solar heat depends on the fixed flow rate configured in the ESR21.
  Trends are reliable, absolute values are not.

Solar heat is **not electricity** — do not add it to the Energy dashboard's
solar panel field.

### Statistics done right

* Real meters (grid, cleaned solar total) use `total_increasing`.
* The solar total is cleaned on the Pi: the raw ESR21 meter contains
  glitches (single readings of 1025 and 2050 MWh) that would otherwise add
  about 1 GWh of phantom yield to the long-term statistics.
* Calculated grand totals use `total`, so a corrected assumption does not
  double the statistics.
* A source that stops reporting becomes *unavailable* instead of showing a
  frozen value.

## Installation

1. HACS → ⋮ → *Custom repositories* → add this repository, category
   *Integration*.
2. Install **Hargassner HSV**, restart Home Assistant.
3. *Settings → Devices & services → Add integration → Hargassner HSV*.
4. Enter the Pi's address, port (8080) and the token. Show the token on the
   Pi with `cat ~/heizung/ha_token`.

Devices can be deselected later under *Configure*, e.g. the electricity
meter if it is already integrated another way.

## License

Apache-2.0
