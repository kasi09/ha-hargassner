#!/usr/bin/env python3
"""Erzeugt strings.json, translations/en.json und translations/de.json aus
einer Tabelle. So fehlt keine Uebersetzung und keine bleibt verwaist.

    python3 tools/uebersetzungen.py
"""
import json
import os

ZIEL = os.path.join(os.path.dirname(__file__), "..", "custom_components", "hargassner_hsv")

# Schluessel: (englisch, deutsch)
SENSOR = {
    "boiler_state": ("Boiler state", "Kesselzustand"),
    "boiler_temp": ("Boiler temperature", "Kesseltemperatur"),
    "boiler_target": ("Boiler target temperature", "Kesselsolltemperatur"),
    "flue_gas_temp": ("Flue gas temperature", "Abgastemperatur"),
    "o2": ("Residual oxygen", "Restsauerstoff"),
    "o2_target": ("Residual oxygen target", "Restsauerstoff Soll"),
    "output": ("Boiler output", "Kesselleistung"),
    "boiler_heat_power": ("Boiler heat (current)", "Kesselwärme aktuell"),
    "feed_rate": ("Fuel feed rate", "Förderrate"),
    "draft_fan": ("Draft fan speed", "Saugzugdrehzahl"),
    "draft_fan_target": ("Draft fan target", "Saugzug Soll"),
    "air": ("Air", "Luftmenge"),
    "air_corrected": ("Air after lambda correction", "Luft nach Lambdakorrektur"),
    "dhw_temp": ("Hot water tank (top)", "Boiler oben"),
    "hk1_flow_temp": ("Heating circuit 1 flow", "Vorlauf HK1"),
    "hk1_flow_target": ("Heating circuit 1 flow target", "Vorlauf HK1 Soll"),
    "room_temp": ("Room temperature", "Raumtemperatur"),
    "outdoor_temp": ("Outdoor temperature (boiler sensor)", "Außentemperatur (Kesselfühler)"),
    "outdoor_avg": ("Outdoor temperature averaged", "Außentemperatur gemittelt"),
    "combustion_efficiency": ("Combustion efficiency", "Feuerungstechnischer Wirkungsgrad"),
    "dhw_mode": ("Hot water mode", "Boiler-Betriebsart"),
    "hk1_mode": ("Heating circuit 1 mode", "HK1-Betriebsart"),
    "feed_screw_current": ("Feed screw current", "Strom Einschubschnecke"),
    "room_discharge_current": ("Room discharge current", "Strom Raumaustragung"),
    "grate_current": ("Grate current", "Strom Schieberost"),
    "cleaning_current": ("Cleaning current", "Strom Putzeinrichtung"),
    "counter_a": ("Counter A", "Zähler A"),
    "counter_b": ("Counter B", "Zähler B"),
    "counter_c": ("Counter C", "Zähler C"),
    "boiler_heat_today": ("Boiler heat today", "Kesselwärme heute"),
    "pellets_today": ("Pellets today", "Pellets heute"),
    "burner_starts_today": ("Burner starts today", "Brennstarts heute"),
    "burn_time_today": ("Full-load time today", "Brenndauer heute"),
    "active_time_today": ("Active time today", "Aktivzeit heute"),
    "boiler_heat_total": ("Boiler heat total", "Kesselwärme gesamt"),
    "pellets_total": ("Pellets total", "Pellets gesamt"),
    "burner_starts_total": ("Burner starts total", "Brennstarts gesamt"),
    "burn_time_total": ("Full-load time total", "Brenndauer gesamt"),
    "collector_temp": ("Collector temperature", "Kollektortemperatur"),
    "tank_bottom_temp": ("Tank bottom temperature", "Speicher unten"),
    "solar_spread": ("Collector-tank spread", "Spreizung"),
    "solar_heat_power": ("Solar heat (current)", "Solarwärme aktuell"),
    "solar_flow": ("Flow rate (fixed setting)", "Volumenstrom (fest eingestellt)"),
    "solar_meter_raw": ("Heat meter ESR21 (raw)", "Wärmemengenzähler ESR21 (roh)"),
    "solar_heat_total": ("Solar heat total", "Solarwärme gesamt"),
    "solar_heat_today": ("Solar heat today", "Solarwärme heute"),
    "solar_pump_hours_today": ("Solar pump runtime today", "Laufzeit Solarpumpe heute"),
    "solar_pump_starts_today": ("Solar pump starts today", "Starts Solarpumpe heute"),
    "grid_import_power": ("Grid import power", "Netzbezug"),
    "grid_export_power": ("Grid export power", "Einspeisung"),
    "grid_net_power": ("Grid net power", "Netto-Bezug"),
    "grid_import_energy": ("Grid import energy (1.8.0)", "Bezug gesamt (1.8.0)"),
    "grid_export_energy": ("Grid export energy (2.8.0)", "Einspeisung gesamt (2.8.0)"),
    "grid_reactive_import_power": ("Reactive power Q+", "Blindleistung Q+"),
    "grid_reactive_export_power": ("Reactive power Q-", "Blindleistung Q-"),
    "grid_reactive_import_energy": ("Reactive energy R+", "Blindenergie R+"),
    "grid_reactive_export_energy": ("Reactive energy R-", "Blindenergie R-"),
    "grid_collection_energy": ("Collection energy (1.128.0)", "Inkasso-Energie (1.128.0)"),
    "grid_import_today": ("Grid import today", "Bezug heute"),
    "grid_export_today": ("Grid export today", "Einspeisung heute"),
    "base_load": ("Base load", "Grundlast"),
    "extra_load_burning": ("Extra load while burning", "Mehrbezug im Brand"),
    "dairy_power": ("Power", "Leistung"),
    "dairy_energy": ("Energy", "Energie"),
    "dairy_energy_today": ("Energy today", "Energie heute"),
    "weather_temperature": ("Temperature", "Temperatur"),
    "weather_apparent_temperature": ("Apparent temperature", "Gefühlte Temperatur"),
    "weather_humidity": ("Humidity", "Luftfeuchte"),
    "weather_precipitation": ("Precipitation", "Niederschlag"),
    "weather_cloud_cover": ("Cloud cover", "Bewölkung"),
    "weather_pressure": ("Pressure", "Luftdruck"),
    "weather_wind": ("Wind speed", "Wind"),
    "weather_gusts": ("Gusts", "Böen"),
    "weather_wind_direction": ("Wind direction", "Windrichtung"),
    "weather_radiation": ("Solar radiation", "Einstrahlung"),
    "weather_code": ("Weather code (WMO)", "Wettercode (WMO)"),
    "age_boiler": ("Data age boiler", "Datenalter Kessel"),
    "age_solar": ("Data age solar", "Datenalter Solar"),
    "age_grid": ("Data age meter", "Datenalter Stromzähler"),
    "age_dairy_room": ("Data age sub-meter", "Datenalter Milchkammer"),
    "age_weather": ("Data age weather", "Datenalter Wetter"),
    "database_size": ("Database size", "Datenbankgröße"),
    "disk_free": ("Free disk space", "Freier Speicher"),
}
ZUSTAENDE = {
    "boiler_state": {
        "off": ("Off", "Heizung aus"), "refill_soon": ("Refill pellets soon", "Pellets bald nachfüllen"),
        "refill": ("Refill pellets", "Pellets nachfüllen"), "grate_check": ("Grate check", "Rost-Zu-Check"),
        "start": ("Boiler start", "Kessel Start"),
        "fuel_feed_ignition_check": ("Fuel feed / ignition check", "ES Fördern / Zündüberwachung"),
        "ignition": ("Ignition", "Zündung"), "full_load": ("Full load", "Leistungsbrand"),
        "ember_hold": ("Ember hold", "Gluterhaltung"), "deashing_prepare": ("Preparing de-ashing", "Entaschung einleiten"),
        "burnout": ("Burnout", "Ausbrand abwarten"), "deashing": ("De-ashing", "Entaschung"),
        "cleaning_start": ("Cleaning start", "Reinigung Start"), "cleaning": ("Cleaning", "Reinigung"),
        "cleaning_end": ("Cleaning end", "Reinigung Ende"), "unknown": ("Unknown", "Unbekannt"),
    },
    "dhw_mode": {"loading": ("Loading", "Wird geladen"), "residual_heat": ("Residual heat", "Restwärme"),
                 "off": ("Off", "Aus"), "other": ("Other", "Sonstiges")},
    "hk1_mode": {"heating": ("Heating", "Heizen"), "residual_heat": ("Residual heat", "Restwärme"),
                 "summer_off": ("Summer shutdown", "Sommerabschaltung"), "setback": ("Setback", "Absenkung"),
                 "off": ("Off", "Aus"), "other": ("Other", "Sonstiges")},
}
BINAER = {
    "solar_pump": ("Solar pump", "Solarpumpe"),
    "service_hsv_logger": ("Service boiler logger", "Dienst Kessel-Logger"),
    "service_hsv_solar": ("Service solar logger", "Dienst Solar-Logger"),
    "service_hsv_strom": ("Service meter logger", "Dienst Strom-Logger"),
    "service_hsv_web": ("Service web", "Dienst Weboberfläche"),
    "service_hsv_waechter": ("Service watchdog", "Dienst Wächter"),
}
GERAETE = {
    "boiler": ("Boiler", "Kessel"), "solar": ("Solar thermal", "Solarthermie"),
    "grid": ("Electricity meter", "Stromzähler"), "dairy_room": ("Dairy room", "Milchkammer"),
    "weather": ("Weather (Open-Meteo)", "Wetter (Open-Meteo)"), "logger": ("Data logger", "Datenlogger"),
}
FELD = {
    "host": ("Host", "Adresse"), "port": ("Port", "Port"), "token": ("Token", "Token"),
}
FELD_HILFE = {
    "host": ("IP address or host name of the Raspberry Pi running hsv-web.",
             "IP-Adresse oder Name des Raspberry Pi, auf dem hsv-web läuft."),
    "port": ("Port of hsv-web, usually 8080.", "Port von hsv-web, meist 8080."),
    "token": ("Shown on the Pi with: cat ~/heizung/ha_token",
              "Auf dem Pi anzeigen mit: cat ~/heizung/ha_token"),
}
FEHLER = {
    "cannot_connect": ("Cannot connect to the Pi.", "Keine Verbindung zum Pi."),
    "invalid_auth": ("The token was rejected.", "Der Token wurde abgelehnt."),
    "unsupported_api": ("The Pi speaks an API version this integration does not support.",
                        "Der Pi spricht eine Schnittstellenversion, die diese Integration nicht kennt."),
}
ABBRUCH = {
    "already_configured": ("This installation is already configured.", "Diese Anlage ist bereits eingerichtet."),
    "reauth_successful": ("Token updated.", "Token aktualisiert."),
    "reconfigure_successful": ("Connection updated.", "Verbindung aktualisiert."),
    "wrong_installation": ("This is a different installation.", "Das ist eine andere Anlage."),
}
AUSNAHMEN = {
    "cannot_connect": ("Cannot connect to the Pi.", "Keine Verbindung zum Pi."),
    "invalid_auth": ("The token was rejected.", "Der Token wurde abgelehnt."),
    "unsupported_api": ("Unsupported Pi API version {version}; please update the integration.",
                        "Nicht unterstützte Schnittstellenversion {version} am Pi; bitte die Integration aktualisieren."),
}


def baue(i):
    def t(paar):
        return paar[i]
    felder = {k: t(v) for k, v in FELD.items()}
    hilfe = {k: t(v) for k, v in FELD_HILFE.items()}
    sensor = {}
    for k, v in SENSOR.items():
        sensor[k] = {"name": t(v)}
        if k in ZUSTAENDE:
            sensor[k]["state"] = {z: t(p) for z, p in ZUSTAENDE[k].items()}
    return {
        "config": {
            "step": {
                "user": {
                    "title": t(("Connect to the data logger", "Mit dem Datenlogger verbinden")),
                    "description": t(("Read-only connection to the Pi that records the boiler.",
                                      "Nur lesende Verbindung zum Pi, der die Heizung aufzeichnet.")),
                    "data": felder, "data_description": hilfe,
                },
                "reauth_confirm": {
                    "title": t(("New token", "Neuer Token")),
                    "data": {"token": felder["token"]},
                    "data_description": {"token": hilfe["token"]},
                },
                "reconfigure": {
                    "title": t(("Change connection", "Verbindung ändern")),
                    "data": felder, "data_description": hilfe,
                },
            },
            "error": {k: t(v) for k, v in FEHLER.items()},
            "abort": {k: t(v) for k, v in ABBRUCH.items()},
        },
        "options": {
            "step": {
                "init": {
                    "title": t(("Devices", "Geräte")),
                    "description": t((
                        "Choose which devices to create. Deselect the meter if it is already integrated elsewhere.",
                        "Wähle, welche Geräte angelegt werden. Den Stromzähler abwählen, wenn er schon anders eingebunden ist.")),
                    "data": {"sources": t(("Devices", "Geräte"))},
                }
            }
        },
        "selector": {"sources": {"options": {k: t(v) for k, v in GERAETE.items()}}},
        "device": {k: {"name": t(v)} for k, v in GERAETE.items()},
        "entity": {
            "sensor": sensor,
            "binary_sensor": {k: {"name": t(v)} for k, v in BINAER.items()},
        },
        "exceptions": {k: {"message": t(v)} for k, v in AUSNAHMEN.items()},
    }


def schreibe(pfad, daten):
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    en, de = baue(0), baue(1)
    schreibe(os.path.join(ZIEL, "strings.json"), en)
    schreibe(os.path.join(ZIEL, "translations", "en.json"), en)
    schreibe(os.path.join(ZIEL, "translations", "de.json"), de)
    print("geschrieben:", len(SENSOR), "Sensoren,", len(BINAER), "Binaersensoren")
