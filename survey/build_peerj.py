"""PeerJ Computer Science version of the manuscript: main.tex (built by build_tex.py) -> main_peerj.tex.
Changes only the wrapper, never the science:
  - elsarticle -> article, with line numbers (PeerJ asks for them) and name-year citations (PeerJ style)
  - Elsevier front matter (highlights, keyword block, journal name) -> title, authors, structured abstract
  - every number in the structured abstract is a generated macro, so it tracks the data
Rules checked on the live PeerJ Computer Science author instructions on 11 Nov 2026: US Letter, 1-inch margins, 12-point Times, left-justified,
line numbers, author cover page as the first page, abstract up to 500 words with bold sub-headings ending in a period, any reference style
(name-year used here), Literature Review sections Introduction / Survey Methodology / topic sections / Conclusions / Acknowledgments / References. Usage: python3 build_peerj.py   (then pdflatex/bibtex, see Makefile target `peerj`)"""
import re
from pathlib import Path
S = Path(__file__).parent
src = (S / "main.tex").read_text()
title = re.search(r"\\title\{(.*?)\}\s*\n", src, re.S).group(1).strip()

ABSTRACT = r"""
\textbf{Background.} Automatic attendance is moving from cards and cameras to phones and radios. Geofencing, which marks a person present when a location fix falls inside a boundary, is now common in attendance applications, and LoRa radios can carry the same logic to devices without a phone. Earlier attendance reviews are mostly organised by sensing modality, and the one geolocation-based review we found is a short narrative without an evidence audit. We ask what the geofence and LPWAN attendance literature reports, how it treats location error and the person being tracked, and whether thin reporting is specific to geofencing.

\textbf{Methods.} We ran \nQueriesAll{} documented queries on \srcPhrase{}, merged \unionUnique{} unique records, applied topic filters to \nStageOne{}, selected \nSelected{} and verified \nVerified{} references against DOI registries. We audited \nAudit{} geofence-based attendance systems from their abstracts and coded the full texts of the \ftN{} whose open-access copy carries a Creative Commons licence against seven questions. \coderAbs{} A comparison group of \nOthersRecent{} other attendance systems since 2018 was coded at abstract level with the same rules. All queries, counts, coding rules and codes are published.

\textbf{Results.} Most audited systems (\pRecent\%) date from 2025--2026. In the full texts, \ftQtwo{} of \ftN{} measure the geofence decision, \ftQone{} handle or analyse location error, \ftQthree{} report an adversarial test, none states a location sampling policy or reports energy, and none uses LoRa. \hfConsent{} of \hfN{} audited abstracts mention consent. Thin reporting is not unique to geofencing: \cmpOacc\% of the other attendance abstracts give an accuracy figure, against \cmpGacc\% of the geofence abstracts. We turn the seven full-text questions into a minimum reporting checklist; \ftScoreZero{} of the \ftN{} papers meet none of its items. A short summary of a companion simulation on real GPS tracks shows what the gaps cost: a plain radius test gives 0.455 false events per track-hour, hysteresis removes about 94\% of them, and ordinary class changes cut the capacity of one LoRa gateway by about 15\%.

\textbf{Conclusions.} Geofence attendance is easy to build and thinly evaluated, as are attendance systems in general. The gaps that matter most are the treatment of boundary error, tests of attacks on the location factor, energy, and the consent and legal position of the person tracked. The checklist and the open research agenda give authors and reviewers a concrete list of what to report and what to measure next.
"""

pre = src[: src.index("\\begin{document}")]
body = src[src.index("\\begin{document}") + len("\\begin{document}"):]
# drop the Elsevier front matter block
body = re.sub(r"\\begin\{frontmatter\}.*?\\end\{frontmatter\}", "@@FRONT@@", body, flags=re.S)
assert "@@FRONT@@" in body, "frontmatter block not found"

pre = pre.replace(r"\documentclass[preprint,12pt]{elsarticle}", r"\documentclass[12pt]{article}")
pre = re.sub(r"\\biboptions\{[^}]*\}\n", "", pre)
pre = re.sub(r"\\journal\{[^}]*\}\n", "", pre)
pre = pre.replace(r"\newcommand{\todo}", r"\usepackage[letterpaper,margin=1in]{geometry}" + "\n" + r"\usepackage{mathptmx}" + "\n" + r"\usepackage{setspace,lineno}" + "\n" +
                  r"\usepackage[authoryear,round]{natbib}" + "\n" + r"\let\cite\citep" + "\n" + r"\newcommand{\todo}", 1)
front = (r"\begin{titlepage}\raggedright" + "\n"
         r"{\Large\bfseries " + title + r"}\par\vspace{1.5em}" + "\n"
         r"Dhanisha S, Lakshmi Harika P\textsuperscript{*}, Adesh Kanna P and Ananyaa S\par\vspace{0.5em}" + "\n"
         r"School of Computer Science and Engineering, Vellore Institute of Technology, Chennai, Tamil Nadu 600127, India\par\vspace{1.5em}" + "\n"
         r"\textsuperscript{*}Corresponding author: Lakshmi Harika P, School of Computer Science and Engineering, Vellore Institute of Technology, Chennai, Tamil Nadu 600127, India; lakshmi.harika@vit.ac.in" + "\n"
         r"\end{titlepage}" + "\n"
         r"\raggedright" + "\n"
         r"\section*{Abstract}" + ABSTRACT + "\n"
         r"\noindent\textbf{Keywords:} attendance, geofencing, GPS, LoRa, LPWAN, Internet of Things, location privacy, survey" + "\n\n"
         r"\linenumbers" + "\n")
body = body.replace("@@FRONT@@", front)
body = body.replace(r"\bibliographystyle{elsarticle-num}", r"\bibliographystyle{plainnat}")
out = pre + "\\begin{document}" + body
(S / "main_peerj.tex").write_text(out)
print("main_peerj.tex written;", len(re.findall(r"\\cite\{", out)), "cite commands (mapped to \\citep)")
