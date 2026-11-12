"""main.src.tex -> main.tex: replace record ids (@123) inside \\cite{...} by verified BibTeX keys. Unknown ids abort the build."""
import json, re, sys
from pathlib import Path
S = Path(__file__).parent
keys = json.load(open(S / "screening/keys.json")); keys.update(json.load(open(S / "screening/aliases.json")))
src = (S / "main.src.tex").read_text()
bad = []
def fix(m):
    out = []
    for k in m.group(1).split(","):
        k = k.strip()
        if k.startswith("@"):
            if k[1:] in keys: k = keys[k[1:]]
            else: bad.append(k)
        out.append(k)
    return "\\cite{" + ",".join(out) + "}"
res = re.sub(r"\\cite\{([^}]*)\}", fix, src)
if bad: sys.exit("unverified ids cited: " + ", ".join(sorted(set(bad))))
(S / "main.tex").write_text(res); print("main.tex written;", len(re.findall(r"\\cite\{", res)), "cite commands")
