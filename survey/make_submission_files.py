"""Generate submission/cover_letter.md and submission/highlights.txt from the manuscript and the generated macros.
Numbers come from gen/*.tex, so the letter tracks the text (including Scopus / Web of Science / IEEE imports and human re-coding).
Anything the authors must decide or confirm is written as [AUTHORS: ...]. The script never sends anything.
  python3 make_submission_files.py"""
import re
from pathlib import Path
S = Path(__file__).parent
OUT = S / "submission"; OUT.mkdir(exist_ok=True)
mac = {}
for f in sorted((S / "gen").glob("stats*.tex")):
    for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{((?:[^{}]|\{[^{}]*\})*)\}", f.read_text()): mac[k] = v
def m(k):
    v = mac[k].replace("{,}", ",").replace("\\emph{", "").replace("}", "").replace("\\%", "%")
    return v
src = (S / "main.src.tex").read_text()

# highlights: Elsevier norm is 3-5 bullets, each at most 85 characters including spaces (confirm in the Guide for Authors)
hl = re.findall(r"\\item (.*)", re.search(r"\\begin\{highlights\}(.*?)\\end\{highlights\}", src, re.S).group(1))
lines = [f"{h}   [{len(h)} characters]" for h in hl]
over = [h for h in hl if len(h) > 85]
(OUT / "highlights.txt").write_text("\n".join(h for h in hl) + "\n")
print(f"highlights: {len(hl)} bullets, longest {max(len(h) for h in hl)} characters", "(OVER 85!)" if over else "(ok)")

human_done = bool(mac.get("humanSentence", "").strip())
external = "Scopus" in mac.get("srcPhrase", "")   # the one database still missing; Web of Science and IEEE Xplore were imported on 11 Nov 2026
search_line = (f"We ran {m('nQueriesAll')} documented queries on {m('srcPhrase')}, merged {m('unionUnique')} unique records, selected {m('nSelected')} "
               f"and verified {m('nVerified')} references against DOI registries.")
gap_line = ("" if external else " [AUTHORS: Scopus, Web of Science and IEEE Xplore have not been searched yet. Run them first (survey/search/external_queries.md), "
            "then regenerate this letter, because this sentence and the manuscript's method section change.]")
coder_line = ("A human who did not write the coding rules re-coded a sample of the abstracts and full texts, and we report the agreement." if human_done else
              f"One author read each of the {m('ftN')} full texts in full and checked every full-text code against the paper; the author saw the AI's codes first, so this is a check and not an independent re-coding. The check changed none of the {m('ftCodes')} codes.")

letter = f"""# Cover letter (draft)

[AUTHORS: date]

To the Editor-in-Chief
*Internet of Things; Engineering Cyber Physical Human Systems*

**Submission: survey paper**
**Title:** {re.search(r"\\title\{(.*?)\}\s*\n", src, re.S).group(1).strip()}
**Authors:** Dhanisha S, Lakshmi Harika P (corresponding, lakshmi.harika@vit.ac.in), Adesh Kanna P, Ananyaa S. School of Computer Science and Engineering, Vellore Institute of Technology, Chennai, Tamil Nadu 600127, India
**Corresponding author:** Lakshmi Harika P, lakshmi.harika@vit.ac.in

Dear Editor,

We submit the manuscript above as a survey paper. Automatic attendance is a people-facing cyber-physical system: a person carries the sensor, a location rule judges them, and a wrong decision has a cost for that person. Geofencing and long-range low-power radios such as LoRa are now common in attendance applications, yet earlier attendance reviews are mostly organised by sensing modality, and the one geolocation-based review we found is a short narrative without an evidence audit.

**What the paper does.** {search_line} We audited {m('nAudit')} geofence-based attendance systems from their abstracts and coded the full texts of the {m('ftN')} whose open-access copy carries a Creative Commons licence. {coder_line} We also coded {m('nOthersRecent')} other attendance systems as a comparison group.{gap_line}

**What it finds.**
1. Of the {m('ftN')} full texts, {m('ftQtwo')} measure the geofence decision and {m('ftQone')} handle location error; {m('ftQthree')} report an attack on the location factor and none reports energy. None of the {m('nAudit')} audited systems uses LoRa.
2. Thin reporting is not specific to geofencing. {m('cmpOacc')}% of the other attendance abstracts give an accuracy figure, against {m('cmpGacc')}% of the geofence abstracts.
3. The person is largely absent from the evidence. {m('hfConsent')} of {m('hfN')} audited abstracts mention consent, and the paper relates the findings to the GDPR and India's Digital Personal Data Protection Act 2023.
4. We propose a seven-item minimum reporting checklist and score the {m('ftN')} full texts against it: {m('ftScoreZero')} meet none of the items.

**Fit with the journal.** The paper sits in the applications block (eLearning and well-being, smart campuses and buildings) and the societal block (ethics, law and regulation, human-technology interaction at scale), with security and privacy from the theory block. Survey papers are a listed article type.

**Overlap and prior work.** A short case study (one table) summarises a companion simulation by the same authors on real GPS tracks and class-change timing. It sizes the problems the survey identifies and is not claimed as a contribution of the survey. [AUTHORS: state its status, for example "available as a preprint at DOI ..." or "under review elsewhere", and cite it in the manuscript.] The companion work is the only overlap; no part of the survey has been published or is under consideration elsewhere [AUTHORS: confirm].

**Reproducibility.** Every query, hit count, screening rule and coding sheet is published with the scripts that generate each number in the text [AUTHORS: add the repository DOI]. Full texts and publisher abstracts are not redistributed.

**Use of AI tools.** An AI assistant was used to write the search and analysis scripts, to apply coding rules, to act as a blind second coder on a sample, and to draft the text. The authors reviewed and edited the content and take responsibility for it; the declaration is in the manuscript. [AUTHORS: confirm this matches what you did and what the journal's current policy requires.]

All authors have approved the manuscript and agree to its submission [AUTHORS: confirm]. We declare no competing interests [AUTHORS: confirm].

**Suggested reviewers** [AUTHORS: add 3-5 with affiliation and institutional email. Pick people who work on geofencing, LPWAN or attendance systems and who are not collaborators, co-authors or from your institution. Do not suggest anyone you have not checked yourselves.]

Sincerely,
Lakshmi Harika P (corresponding author), on behalf of Dhanisha S, Adesh Kanna P and Ananyaa S
"""
(OUT / "cover_letter.md").write_text(letter)

title_txt = re.search(r"\\title\{(.*?)\}\s*\n", src, re.S).group(1).strip()
# ---- PeerJ Computer Science version of the letter (soundness-based review: lead with method, data and limits, not novelty)
pj = f"""# Cover letter for PeerJ Computer Science (draft)

[AUTHORS: date]

To the Editors, PeerJ Computer Science

**Article type:** Literature Review
**Title:** {title_txt}
**Authors:** Dhanisha S, Lakshmi Harika P (corresponding, lakshmi.harika@vit.ac.in), Adesh Kanna P, Ananyaa S. School of Computer Science and Engineering, Vellore Institute of Technology, Chennai, Tamil Nadu 600127, India
**Corresponding author:** Lakshmi Harika P, lakshmi.harika@vit.ac.in

Dear Editors,

We submit the manuscript above as a Literature Review. It maps the literature on GPS-geofence and LPWAN attendance sensing and tests what the evidence in that literature supports.

**Use of generative AI, stated up front.** An AI assistant (Claude, Anthropic; exact versions in Section 2.5 and the Declarations [AUTHORS: confirm]) was used to write the search, screening and analysis scripts, to apply the published coding rules as first coder on abstracts and on short extracts of open-access full texts, as a blind second coder on a sample, and to draft and format the text. We describe this in the Methods as PeerJ's policy for literature reviews asks. Safeguards, all in the supplementary files: the rules and every coding sheet are published, so any code can be checked and re-run; every number in the text is generated from those files; the blind AI second coder agreed on {m('agPct')}% of {m('agJ')} judgements over {m('agN')} papers (Cohen's kappa {m('agKappa')}) and the one disagreement was resolved by rereading the paper; {coder_line} Because PeerJ asks for permission before copyrighted material goes into an AI tool and we have not obtained it, the full-text results rest only on the {m('ftLicCC')} papers that carry a Creative Commons licence; the AI saw short extracts of {m('ftLicNone')} further free-to-read papers in a first pass, and their codes are not used anywhere in the article. The recorded licence of every paper is in the supplementary files. No person outside the author team re-coded the papers, and the article says so. The prompts and session records are kept and will be given to the editor on request. The authors, not the assistant, are responsible for the content and the references.

**Method.** {search_line} We audited {m('nAudit')} geofence-based attendance systems from their abstracts and coded the full texts of the {m('ftN')} whose open-access copy carries a Creative Commons licence against seven questions, with a comparison group of {m('nOthersRecent')} other attendance systems. {coder_line} Every query, hit count, screening rule and coding sheet is published, and every number in the text is generated from the data files.{gap_line}

**Findings.** Of the {m('ftN')} full texts, {m('ftQtwo')} measure the geofence decision and {m('ftQone')} handle location error; {m('ftQthree')} report an attack on the location factor and none reports energy. None of the {m('nAudit')} audited systems uses LoRa. Thin reporting is not specific to geofencing ({m('cmpOacc')}% of other attendance abstracts give an accuracy figure, against {m('cmpGacc')}% of the geofence abstracts). We propose a seven-item minimum reporting checklist; {m('ftScoreZero')} of the {m('ftN')} papers meet none of its items.

**Limits we state in the paper.** The audit is abstract-level for {m('nAudit')} systems and full-text for {m('ftN')}; abstract-level coding cannot show that a property is absent from a paper. The checklist was derived from the same papers it scores, so its counts describe reporting and do not validate it. A short case study summarises a companion simulation by the same authors; it sizes the problems and is not claimed as a contribution of this review.

**Data and code.** All raw data and code are deposited at [AUTHORS: repository DOI]. Publishers' abstracts and the full texts are not redistributed; the deposit contains record identifiers, queries, counts, codes and the scripts that regenerate every table [AUTHORS: confirm with the editorial office that this satisfies the raw-data rule].

**Overlap and conflicts.** The companion simulation is the only overlap; no part of this review is published or under consideration elsewhere [AUTHORS: confirm and state the status of the companion paper]. We declare no competing interests [AUTHORS: confirm]. All authors approved the submission [AUTHORS: confirm].

**Suggested reviewers** (optional) [AUTHORS: 3-5 people who work on geofencing, LPWAN or attendance systems and who are not collaborators; do not suggest anyone you have not checked yourselves.]

Sincerely,
Lakshmi Harika P (corresponding author), on behalf of Dhanisha S, Adesh Kanna P and Ananyaa S
"""
(OUT / "cover_letter_peerj.md").write_text(pj)

print("wrote submission/cover_letter.md, cover_letter_peerj.md and highlights.txt")
