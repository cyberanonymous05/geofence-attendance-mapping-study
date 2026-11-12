# Data and code for the survey on GPS geofence and LPWAN attendance sensing

Built 2026-11-12 (mode: safe). Licences: data and text CC-BY-4.0 (see `LICENSE-DATA`), code MIT (see `LICENSE-CODE`).

## Layout
- `survey/` manuscript source (`main.src.tex`), the scripts that make every number and table (`make_*.py`, `analysis_*.py`), `Makefile`.
- `survey/search/` the search scripts, `query_log.csv` (every query with its hit count), `prisma_counts.json`, `sources_counts.json`, the merged corpus, and the OpenAlex responses (`raw/`, CC0).
- `survey/screening/` screening and audit scripts, `audit.csv` (the 60 audited systems), `fulltext_codes_*.csv` (full-text codes of coder 1, the blind AI coder, and the adjudicated result), `agreement.json`, `verification_log.csv` (DOI check of every reference), `keys.json`.
- `survey/gen/` generated tables and macros that the text includes.
- `sim/` the simulator code and result files behind the case study (`survey/check_case_numbers.py` checks the quoted numbers against them).

## Reproduce
`cd survey && make tables pdf && make check` rebuilds the tables, the PDF, and checks the case-study numbers against `sim/results`.
Re-running the searches (`make search corpus`) returns newer data, so counts will differ from the published run.

## What is NOT in this bundle
- Full texts of the audited papers (read from open-access copies; not redistributed). `screening/fulltext_status.csv` records which could be read.
- The GeoLife and StudentLife datasets used by the simulator (`sim/data/`). Fetch them from their owners under their terms.
- Hardware files.
- Database exports: in safe mode `search/external_ids/` holds the Scopus, Web of Science and IEEE Xplore exports with the abstract and keyword columns removed (titles, authors, years, DOIs and identifiers are kept). The unstripped exports are the publishers' text and are not redistributed; re-run the queries in `search/external_queries.md` to get them.
- Abstracts: in safe mode the `abstract` column is blank in these CSVs: survey/search/corpus.csv, survey/search/corpus_all.csv, survey/screening/stage1.csv. Re-fetch with `make search corpus`.
- Crossref, arXiv and Semantic Scholar raw responses (`search/raw_other/`): same reason.

## Notes
- Part of the coding is judgement: the selection id lists in `screening/build_bib.py` and two hand-coded audit fields in `screening/audit_code.py`.
- The second full-text coder was an AI model that saw snippets only. Full-text results use only the 17 papers with a Creative Commons licence; the codes for the 11 other free-to-read papers stay in the data files for completeness and are used in no reported result. The human re-coding kit is not included yet.
