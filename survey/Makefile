# Reproduce the numbers and tables. The search steps need no keys or logins; re-running them later returns newer data, so counts differ.
.PHONY: search corpus screen bib fulltext tables check external
search:   ; cd search && python3 search_openalex.py && python3 search_more.py && python3 search_sources.py && python3 merge_sources.py
corpus:   ; cd search && python3 build_corpus.py && python3 merge_sources.py && python3 stage1.py
screen:   ; cd screening && python3 audit_code.py
bib:      ; cd screening && python3 build_bib.py && python3 patch_authors.py && python3 audit_code.py
# full texts go to a scratch dir outside the repo and are never redistributed: make fulltext SCR=/tmp/ft
fulltext: ; cd screening && python3 oa_meta.py && python3 fulltext_fetch.py $(SCR)/ft && python3 -I fulltext_snips.py $(SCR)/ft $(SCR)/snips
tables:   ; python3 make_survey_tables.py && python3 analysis_extra.py && python3 make_fulltext_table.py && python3 make_fig_reporting.py
check:    ; python3 check_case_numbers.py
external: ; cd search && python3 import_exports.py && python3 merge_sources.py && python3 stage1.py && cd ../screening && python3 audit_code.py && python3 build_bib.py && python3 patch_authors.py && python3 audit_code.py
