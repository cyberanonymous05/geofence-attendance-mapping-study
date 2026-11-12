"""All model parameters in one place. Each carries its source/status.

STATUS KEY: DATASHEET = typical value from manufacturer datasheet (cite in paper);
ASSUMED = engineering assumption, must be justified or swept in the paper;
STANDARD = from a published standard/formula.
"""

# ---- Campus / fence (ASSUMED) ----
FENCE_RADIUS_M = 300.0          # circular campus/hostel fence
WALK_SPEED_MPS = 1.4            # mean pedestrian speed (ASSUMED, common literature value)
V_MAX_MPS = 3.0                 # speed bound used by adaptive sampler (ASSUMED, jog/cycle)

# ---- GPS error (ASSUMED; replace with cited distribution before submission) ----
GPS_SIGMA_OPEN_M = 2.1          # ~ 2.5 m CEP / 1.18 (Neo-6M datasheet CEP 2.5 m)
GPS_SIGMA_DEGRADED_M = 8.0      # near buildings / tree cover
GPS_CORR_TAU_S = 30.0           # error autocorrelation time (ASSUMED)
GPS_OUTLIER_P = 0.005           # prob. of a multipath outlier fix
GPS_OUTLIER_SIGMA_M = 40.0

# ---- Energy (DATASHEET typical values) ----
V_SUPPLY = 3.3
I_GPS_ACTIVE_A = 0.047          # u-blox NEO-6M typical acquisition current, 47 mA (datasheet GPS.G6-HW-09005, Table 11)
GPS_FIX_TIME_S = 2.0            # hot-start fix time with backup supply (ASSUMED)
I_LORA_TX_A = 0.120             # SX1278 +20 dBm
I_LORA_RX_A = 0.0125
I_SLEEP_A = 0.00003             # sleep: GPS backup 22 uA (datasheet, V_BCKP=1.8 V) + ~8 uA MCU/radio sleep (ASSUMED)
BATTERY_MAH = 1000.0            # 1000 mAh Li-ion (ASSUMED)
BATTERY_USABLE = 0.8            # derating

# ---- LoRa (STANDARD: Semtech SX127x) ----
LORA_BW_HZ = 125_000
LORA_CR = 1                     # 4/5
LORA_PREAMBLE = 8
LORA_CRC = True
LORA_EXPLICIT_HEADER = True
