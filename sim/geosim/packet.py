"""Authenticated, confidential event packet, 10 bytes:  id(2) | sa(1) | counter(3) | mac(4).

sa = state bit (MSB) and age (7 bits, 2 s units, 0..254 s): seconds between the first confirming fix and the
moment of transmission, which lets the server back-date the event even when the node delays the packet.
sa is XORed with a per-packet keystream byte HMAC-SHA256(K, 'ks'|counter)[0] (a PRF stream; a deployment would use
AES-CTR as in LoRaWAN), and the tag is HMAC-SHA256(K, id|sa_enc|counter) truncated to 4 bytes (encrypt-then-MAC).
The receiver enforces a strictly increasing counter (replay defence). Without the key, an eavesdropper sees the
pseudonymous id and the transmission time, but neither the state nor the age."""
import hmac, hashlib

PAYLOAD_BYTES = 10
AGE_UNIT_S = 2
AGE_MAX_S = 127 * AGE_UNIT_S


def _ks(key: bytes, counter: int) -> int:
    return hmac.new(key, b"ks" + counter.to_bytes(3, "big"), hashlib.sha256).digest()[0]


def build(key: bytes, node_id: int, inside: bool, counter: int, age_s: float = 0.0) -> bytes:
    age = min(int(round(max(age_s, 0.0) / AGE_UNIT_S)), 127)
    sa = ((1 if inside else 0) << 7) | age
    enc = sa ^ _ks(key, counter)
    body = node_id.to_bytes(2, "big") + bytes([enc]) + counter.to_bytes(3, "big")
    mac = hmac.new(key, body, hashlib.sha256).digest()[:4]
    return body + mac


class Receiver:
    def __init__(self, keys):
        self.keys = keys
        self.last = {}

    def accept_ext(self, pkt: bytes):
        """Returns (node_id, inside, counter, age_s) or None."""
        if len(pkt) != PAYLOAD_BYTES:
            return None
        body, mac = pkt[:6], pkt[6:]
        nid = int.from_bytes(body[:2], "big")
        key = self.keys.get(nid)
        if key is None:
            return None
        if not hmac.compare_digest(hmac.new(key, body, hashlib.sha256).digest()[:4], mac):
            return None
        ctr = int.from_bytes(body[3:6], "big")
        if ctr <= self.last.get(nid, -1):
            return None
        self.last[nid] = ctr
        sa = body[2] ^ _ks(key, ctr)
        return nid, bool(sa >> 7), ctr, (sa & 0x7F) * AGE_UNIT_S

    def accept(self, pkt: bytes):
        r = self.accept_ext(pkt)
        return None if r is None else r[:3]
