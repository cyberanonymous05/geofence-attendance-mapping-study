# Reproduce the survey. Network steps (search, bib, fulltext) need no keys or logins; re-running them later returns newer data,
# so counts will differ; raw responses of the published run are in search/raw and search/raw_other.
.PHONY: all search corpus screen bib fulltext tables pdf check external humankit submission peerj
all: tables pdf
search:   ; cd search && python3 search_openalex.py && python3 search_more.py && python3 search_sources.py && python3 merge_sources.py
corpus:   ; cd search && python3 build_corpus.py && python3 merge_sources.py && python3 stage1.py
screen:   ; cd screening && python3 audit_code.py
bib:      ; cd screening && python3 build_bib.py && python3 patch_authors.py && python3 audit_code.py
# full texts go to a scratch dir outside the repo (not redistributed); pass its path, e.g. make fulltext SCR=/tmp/ft
fulltext: ; cd screening && python3 oa_meta.py && python3 fulltext_fetch.py $(SCR)/ft && python3 -I fulltext_snips.py $(SCR)/ft $(SCR)/snips
tables:   ; python3 make_survey_tables.py && python3 analysis_extra.py && python3 analysis_human.py && python3 make_fulltext_table.py && python3 make_fig_reporting.py
pdf:      ; rm -f main.bbl main.aux && python3 build_tex.py && pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
check:    ; python3 check_case_numbers.py
# After saving Scopus / Web of Science / IEEE Xplore exports in search/external/ (see search/external_queries.md):
external: ; cd search && python3 import_exports.py && python3 merge_sources.py && python3 stage1.py && cd ../screening && python3 audit_code.py && python3 build_bib.py && python3 patch_authors.py && python3 audit_code.py
humankit: ; python3 make_human_kit.py
# After the human coder returns coding_sheet_*_done.csv:  python3 human_agreement.py <abstracts_done.csv> <fulltext_done.csv>  then  make tables pdf
# Graphical abstract, highlights and cover letter draft (submission/); data bundle for Zenodo: python3 release/make_release.py --data-licence ... --code-licence ...
submission: ; python3 make_graphical_abstract.py && python3 make_submission_files.py
# PeerJ Computer Science version (line numbers, name-year references, structured abstract): main_peerj.pdf
peerj:    ; rm -f main_peerj.bbl main_peerj.aux && python3 build_peerj.py && pdflatex -interaction=nonstopmode main_peerj.tex && bibtex main_peerj && pdflatex -interaction=nonstopmode main_peerj.tex && pdflatex -interaction=nonstopmode main_peerj.tex
