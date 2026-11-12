"""Node energy model (datasheet-typical currents; see params.py)."""
from . import params as P
from .lora import time_on_air


def battery_joules():
    return P.BATTERY_MAH / 1000.0 * 3600.0 * P.V_SUPPLY * P.BATTERY_USABLE


def daily_energy_j(fixes_per_day, tx_per_day, payload_bytes, sf=7):
    on_s = min(P.GPS_FIX_TIME_S, 86400.0 / max(fixes_per_day, 1e-9))   # GPS cannot be on longer than the interval
    e_gps = fixes_per_day * P.V_SUPPLY * P.I_GPS_ACTIVE_A * on_s
    e_tx = tx_per_day * P.V_SUPPLY * P.I_LORA_TX_A * time_on_air(payload_bytes, sf=sf)
    e_sleep = 86400 * P.V_SUPPLY * P.I_SLEEP_A
    return e_gps + e_tx + e_sleep, {"gps": e_gps, "tx": e_tx, "sleep": e_sleep}


def battery_life_days(fixes_per_day, tx_per_day, payload_bytes, sf=7):
    e, _ = daily_energy_j(fixes_per_day, tx_per_day, payload_bytes, sf)
    return battery_joules() / e
