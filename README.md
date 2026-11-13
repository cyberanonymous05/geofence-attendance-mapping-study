# Data and code for: Presence sensing with GPS geofences and LPWAN for automatic attendance

Data and text: CC-BY-4.0 (`LICENSE-DATA`). Code: MIT (`LICENSE-CODE`).

## Contents
- `survey/search/`: search scripts, `query_log.csv` (every query with its hit count), `prisma_counts.json`, `sources_counts.json`, the merged record lists (`corpus.csv`, `corpus_all.csv`; titles, years, venues, DOIs; abstract column blank), the OpenAlex responses without abstract text (`raw/`), and one DOI-only list per Scopus, Web of Science or IEEE Xplore export (`external_dois/`).
- `survey/screening/`: screening and audit scripts, `audit.csv` (the 60 audited systems), the full-text codes (`fulltext_codes_coder1.csv`, `fulltext_codes_coder2_blind_raw.csv`, `fulltext_codes_final.csv`), `agreement.json`, `fulltext_licences.csv`, `fulltext_status.csv`, `verification_log.csv` (DOI check of every reference).
- `survey/gen/`: the tables, figures and number macros that the manuscript includes.
- `survey/*.py`, `survey/Makefile`, `survey/main.src.tex`: scripts that make every table and number, and the manuscript source that `check_case_numbers.py` compares with the case-study results.
- `sim/`: code, tests and summary result files of the companion simulation behind the case study.

## Reproduce
- Works from this deposit alone: `cd survey && make check` checks every number quoted in the case study against `sim/results`. `python3 make_fulltext_table.py && python3 make_fig_reporting.py` rebuild the full-text table, the checklist table and the figure from the published codes.
- Needs the publishers' abstracts, which this deposit does not contain: `make tables` (the abstract-level tables). Run `make search corpus` first to fetch the abstracts again; this returns newer data, so counts will differ from the published run. The tables and number macros of the published run are in `survey/gen/`, and the abstract-level codes of the 60 audited systems are in `survey/screening/audit.csv`.

## Not included
- Full texts of the audited papers (read from open-access copies).
- Publishers' abstracts: the `abstract` column is blank and the OpenAlex abstract text is removed. `make search corpus` fetches them again.
- The Scopus, Web of Science and IEEE Xplore exports (their licence terms restrict redistribution). Re-run the queries in `survey/search/external_queries.md`.
- Crossref, arXiv and Semantic Scholar raw responses.
- The GeoLife and StudentLife data sets and the per-student event file derived from StudentLife (`sim/data/`). Fetch the data sets from their owners under their terms.
- Hardware files.

## Notes
- Part of the coding is judgement: the selection id lists in `survey/screening/build_bib.py` and two hand-coded audit fields in `survey/screening/audit_code.py`.
- The coders were an AI model (first coder; blind second coder on a sample) that saw abstracts and short snippets only. One author checked all 17 Creative Commons full-text codes after seeing them; no person outside the author team re-coded anything. Full-text results use only the 17 papers with a Creative Commons licence; the codes for the 11 other free-to-read papers stay in the data files and are used in no reported result.
