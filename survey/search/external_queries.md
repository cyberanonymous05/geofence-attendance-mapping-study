# Queries for databases that need institutional access

Run each query, export **with abstracts**, save in `search/external/` as `<db>_<id>.<ext>` and run `python3 import_exports.py`.

- **Scopus** (library login): Advanced search, paste the query, Export > CSV, select *Citation information* and *Abstract & keywords*. Up to 20,000 records per export.
- **Web of Science** (library login): Advanced search, paste the query, Export > Tab-delimited file (Win, UTF-8), record content *Full Record*, up to 1,000 records per file (export in batches).
- **IEEE Xplore** (free to search, no login needed for abstracts): Command search, paste the query, Export > CSV (Citations and abstracts), up to 2,000 per export.
- ScienceDirect and ACM DL block automated access and have no useful bulk export; skip them or add a few records by hand.

## Scopus

- `scopus_S1`: `TITLE-ABS-KEY ( ( geofenc* OR "geo-fenc*" ) AND ( attendance OR "presence monitoring" OR "presence system" ) ) AND PUBYEAR > 2004`
- `scopus_S2`: `TITLE-ABS-KEY ( ( lora OR lorawan OR lpwan ) AND ( attendance OR "roll call" ) ) AND PUBYEAR > 2004`
- `scopus_S3`: `TITLE-ABS-KEY ( ( gps OR gnss ) AND "attendance system" ) AND PUBYEAR > 2004`
- `scopus_S4`: `TITLE-ABS-KEY ( ( lora OR lorawan ) AND ( geofenc* OR "geo-fenc*" ) ) AND PUBYEAR > 2004`
- `scopus_S5`: `TITLE-ABS-KEY ( geofenc* AND ( "location error" OR "gps error" OR "positioning error" OR uncertainty OR hysteresis OR "false alarm*" ) ) AND PUBYEAR > 2004`
- `scopus_S6`: `TITLE ( attendance ) AND TITLE-ABS-KEY ( survey OR review OR "systematic review" ) AND PUBYEAR > 2004`
- `scopus_S7`: `TITLE-ABS-KEY ( ( rfid OR "face recognition" OR bluetooth OR ble OR "qr code" OR nfc OR fingerprint ) AND "attendance system" ) AND PUBYEAR > 2017`
- `scopus_S8`: `TITLE-ABS-KEY ( ( lorawan OR lora ) AND ( scalab* OR collision* OR capacity ) ) AND DOCTYPE ( ar OR re ) AND PUBYEAR > 2014`

## Web of Science

- `wos_W1`: `TS=((geofenc* OR "geo-fenc*") AND (attendance OR "presence monitoring" OR "presence system")) AND PY=(2005-2026)`
- `wos_W2`: `TS=((lora OR lorawan OR lpwan) AND (attendance OR "roll call")) AND PY=(2005-2026)`
- `wos_W3`: `TS=((gps OR gnss) AND "attendance system") AND PY=(2005-2026)`
- `wos_W4`: `TS=((lora OR lorawan) AND (geofenc* OR "geo-fenc*")) AND PY=(2005-2026)`
- `wos_W5`: `TS=(geofenc* AND ("location error" OR "gps error" OR "positioning error" OR uncertainty OR hysteresis OR "false alarm*")) AND PY=(2005-2026)`
- `wos_W6`: `TI=(attendance) AND TS=(survey OR review OR "systematic review") AND PY=(2005-2026)`

## IEEE Xplore

- `ieee_I1`: `("All Metadata":geofenc*) AND ("All Metadata":attendance)`
- `ieee_I2`: `("All Metadata":lora OR "All Metadata":lorawan) AND ("All Metadata":attendance)`
- `ieee_I3`: `("All Metadata":gps) AND ("All Metadata":"attendance system")`
- `ieee_I4`: `("All Metadata":lora OR "All Metadata":lorawan) AND ("All Metadata":geofenc*)`
- `ieee_I5`: `("All Metadata":geofenc*) AND ("All Metadata":"location error" OR "All Metadata":"gps error" OR "All Metadata":hysteresis)`
