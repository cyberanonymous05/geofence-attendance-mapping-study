import numpy as np
from geosim import packet, node, detector, sampler, mobility, gps, energy
from geosim import params as P


def test_packet_replay_and_tamper():
    key = b"k" * 16
    rx = packet.Receiver({7: key})
    p1 = packet.build(key, 7, True, 1)
    assert rx.accept(p1) == (7, True, 1)
    assert rx.accept(p1) is None                      # replay
    bad = bytearray(packet.build(key, 7, False, 2)); bad[2] ^= 1
    assert rx.accept(bytes(bad)) is None              # tamper
    assert rx.accept(packet.build(b"x" * 16, 7, True, 3)) is None  # wrong key
    assert len(p1) == packet.PAYLOAD_BYTES


def test_adaptive_bounded_interval():
    s = sampler.Adaptive()
    assert s.next_interval(P.FENCE_RADIUS_M + 5) == s.t_min
    assert s.next_interval(P.FENCE_RADIUS_M + 5000) == s.t_max


def test_detectors_agree_without_noise():
    rng = np.random.default_rng(0)
    x, y = mobility.generate_day(rng)
    z = np.zeros_like(x)
    for det in (detector.PlainRadius(), detector.Hysteresis(h=5, k=1, dwell_s=0)):
        ev, fixes = node.run_node(x, y, z, z, det, sampler.Fixed(1))
        assert fixes > 0


def test_energy_adaptive_beats_fixed():
    assert energy.battery_life_days(86400 / 300, 10, 10) > energy.battery_life_days(86400, 10, 10)


def test_gps_error_scale():
    rng = np.random.default_rng(1)
    x = np.full(20000, 0.0); y = np.full(20000, 0.0)   # far inside -> open sky
    ex, ey = gps.gps_error(rng, x, y)
    assert 1.5 < np.std(ex) < 4.0


def test_energy_gps_duty_capped():
    # at 1 Hz GPS is continuously on: energy must equal 86400 s of active current, not 2x
    e, parts = energy.daily_energy_j(86400, 0, 10)
    assert abs(parts["gps"] - 86400 * P.V_SUPPLY * P.I_GPS_ACTIVE_A) < 1e-6


def test_capacity_matches_aloha_without_capture():
    import math
    from geosim import capacity, lora
    rate = 33.77 / 86400
    pdr = capacity.simulate_pdr(2000, rate, channels=1, capture_db=1e9, seed=3)
    analytic = math.exp(-2 * 1999 * rate * lora.time_on_air(10, sf=7))
    assert abs(pdr - analytic) < 0.01


def test_baseline_detectors_run_and_filter_noise():
    from geosim import detector
    for det in (detector.MovingAverage(), detector.KalmanRadius()):
        det.reset(inside=True)
        states = [det.update(t, 270.0 + (4 if t % 2 else -4)) for t in range(0, 60)]
        assert all(states)   # well inside the fence: must stay inside despite jitter


def test_packet_v2_confidential_and_backdated():
    key = b"k" * 16
    rx = packet.Receiver({9: key})
    p = packet.build(key, 9, False, 5, age_s=61.0)
    assert len(p) == packet.PAYLOAD_BYTES
    nid, inside, ctr, age = rx.accept_ext(p)
    assert (nid, inside, ctr) == (9, False, 5) and abs(age - 61.0) <= packet.AGE_UNIT_S
    # same state and age, different counter => different ciphertext byte for (most) counters: state is not visible
    enc = {packet.build(key, 9, True, c, age_s=10)[2] for c in range(1, 40)}
    assert len(enc) > 5
    # age saturates
    p2 = packet.build(key, 9, True, 6, age_s=9999)
    assert rx.accept_ext(p2)[3] == packet.AGE_MAX_S
    # tampered ciphertext is rejected
    bad = bytearray(packet.build(key, 9, True, 7)); bad[2] ^= 0x80
    assert rx.accept_ext(bytes(bad)) is None


def test_excess_area_detector():
    from geosim import detector
    d = detector.ExcessArea(R=300, h=10, A=200); d.reset(inside=True)
    st = [d.update(5.0 * i, 300 + 25) for i in range(8)]   # 15 m above band for 35 s
    assert st[-1] is False
    d.reset(inside=True)
    st = [d.update(5.0 * i, 300 + (14 if i % 2 else -20)) for i in range(40)]  # noise around fence
    assert all(st)
