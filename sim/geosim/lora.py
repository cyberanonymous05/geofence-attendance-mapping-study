"""LoRa time-on-air (Semtech SX127x datasheet / AN1200.13) and ALOHA capacity."""
import math


def time_on_air(payload_bytes: int, sf: int = 7, bw_hz: int = 125_000, cr: int = 1,
                preamble: int = 8, crc: bool = True, explicit_header: bool = True) -> float:
    """Packet airtime in seconds."""
    t_sym = (2 ** sf) / bw_hz
    de = 1 if (sf >= 11 and bw_hz == 125_000) else 0   # low data rate optimise
    ih = 0 if explicit_header else 1
    num = 8 * payload_bytes - 4 * sf + 28 + 16 * (1 if crc else 0) - 20 * ih
    n_payload = 8 + max(math.ceil(num / (4 * (sf - 2 * de))) * (cr + 4), 0)
    t_preamble = (preamble + 4.25) * t_sym
    return t_preamble + n_payload * t_sym


def aloha_success_prob(n_nodes: int, rate_per_node_hz: float, toa_s: float) -> float:
    """Pure-ALOHA success probability for one packet among n_nodes identical senders.

    P = exp(-2 * G_others), G_others = (n-1) * rate * ToA (vulnerable period 2*ToA).
    Single channel, single SF, no capture effect (conservative).
    """
    g_others = max(n_nodes - 1, 0) * rate_per_node_hz * toa_s
    return math.exp(-2.0 * g_others)
