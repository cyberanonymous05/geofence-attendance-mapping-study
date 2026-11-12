"""Build evidence snippets per codebook question from downloaded OA full texts (scratch dir; not redistributed).
Usage: python3 -I fulltext_snips.py <scratch_ft_dir> <out_dir>"""
import csv, re, sys
from pathlib import Path
SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
Q = {
 "Q1 location-error handling": r"(gps|location|position\w*)[^.]{0,40}(error|inaccura\w*|uncertain\w*|drift|noise)|buffer|tolerance|margin of|accuracy (threshold|radius)|urban canyon|multipath|signal (loss|weak)|retry|fallback|weak signal",
 "Q2 geofence-decision measurement": r"(geofenc\w*|geo-fenc\w*|location|boundary|in/out|inside|outside)[^.]{0,80}(accura\w*|success rate|false (accept|reject|positive|negative)|precision|recall)|confusion matrix|test (case|scenario)s?|\d+\s+(trials|tests|scenarios|test cases)",
 "Q3 adversarial test": r"fake gps|mock location|spoof\w*|vpn|emulator|rooted|developer options|buddy|penetration|bypass|attack",
 "Q4 location sampling policy": r"(update|polling|sampling|interval|refresh)[^.]{0,60}\d+\s?(s|sec|seconds|ms|min|minutes)\b|every \d+\s?(s|sec|seconds|minutes)|requestLocationUpdates|fused location|priority_\w+|battery optimi[sz]ation",
 "Q5 energy": r"battery|energy|power consumption|mah\b|drain",
 "Q6 privacy": r"privacy|consent|gdpr|data protection|anonymi\w+|personal data|retention|encrypt\w*",
 "Q7 fence parameters": r"radius[^.]{0,40}\d+\s?(m|meter|metre|km)|\d+\s?(m|meter|metre)s?\s+radius|polygon|vertices|latitude[^.]{0,40}longitude",
}
status = {r["id"]: r for r in csv.DictReader(open("fulltext_status.csv"))}
ids = [i for i, r in status.items() if r["status"] == "fulltext"]
for i in ids:
    t = re.sub(r"\s+", " ", (SRC / i / "text.txt").read_text(errors="ignore"))
    # drop reference list: cut at last 'References' heading if it is in the final 30% of the text
    k = max(t.lower().rfind("references"), t.lower().rfind("bibliography"))
    if k > 0.7 * len(t): t = t[:k]
    out = [f"PAPER {i}  ({len(t)} chars of body text)"]
    for q, pat in Q.items():
        hits = [m for m in re.finditer(pat, t, re.I)]
        out.append(f"\n## {q}  [{len(hits)} keyword hits]")
        last = -10**9; n = 0
        for m in hits:
            if m.start() - last < 600: continue
            last = m.start(); n += 1
            out.append("- ..." + t[max(0, m.start() - 130): m.end() + 150] + "...")
            if n >= (2 if q.startswith(("Q5", "Q6")) else 3): break
    (OUT / f"{i}.txt").write_text("\n".join(out))
print(len(ids), "papers")
