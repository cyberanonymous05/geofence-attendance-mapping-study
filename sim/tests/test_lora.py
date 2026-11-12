import math
from geosim.lora import time_on_air, aloha_success_prob

# Reference values from the Semtech LoRa calculator (BW125, CR4/5, 8 preamble, CRC, explicit hdr)
def test_toa_sf7_10b():
    assert math.isclose(time_on_air(10, sf=7), 0.041216, rel_tol=1e-3)

def test_toa_sf12_10b():
    assert math.isclose(time_on_air(10, sf=12), 0.991232, rel_tol=1e-3)

def test_toa_monotonic_in_sf():
    vals = [time_on_air(12, sf=s) for s in range(7, 13)]
    assert vals == sorted(vals)

def test_aloha_limits():
    assert aloha_success_prob(1, 1.0, 0.05) == 1.0
    assert aloha_success_prob(100, 0.01, 0.05) < aloha_success_prob(10, 0.01, 0.05)
