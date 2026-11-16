#!/usr/bin/env python3
"""tools/fetch_fonts.py — download rostered OFL faces into fonts/, emit fonts.css + manifest."""
import json, re, sys, textwrap, urllib.request, zipfile, io, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"

GW = "https://gwfh.mranftl.com/api/fonts/{id}?download=zip&variants={variants}&formats=woff2"
ROSTER_GOOGLE = {
    "geist": [400, 500, 700],
    "geist-mono": [400, 600, 700],
    "inter-tight": [400, 500, 600],
    "jetbrains-mono": [400, 600],
    "instrument-serif": [400],
    "inter": [400, 500, 600],
    "archivo-black": [400],
    "archivo": [400, 500, 600, 700],
    "fraunces": [400, 600, 900],
    "big-shoulders": [400, 600, 800],
    "space-grotesk": [400, 500, 700],
    "syne": [500, 700, 800],
    "bodoni-moda": [400, 600],
    "jost": [300, 400, 500],
    "baloo-2": [500, 700, 800],
    "poppins": [400, 500, 600],
    "caveat": [500, 700],
    "prata": [400],
    "ibm-plex-sans": [400, 500, 600],
    "ibm-plex-mono": [400, 500],
    "dm-sans": [400, 500, 700],
    "space-mono": [400, 700],
    "nunito": [400, 600, 700],
    "unbounded": [400, 600, 800],
}
FS_FAMILY = {"clash-display": "Clash Display", "satoshi": "Satoshi", "general-sans": "General Sans", "sentient": "Sentient"}
ROSTER_FONTSHARE = {
    "clash-display": [400, 500, 600, 700],
    "satoshi": [400, 500, 700],
    "general-sans": [400, 500, 600],
    "sentient": [400, 500, 700],
}
DISPLAY_NAME = {
    "geist": "Geist", "geist-mono": "Geist Mono", "inter-tight": "Inter Tight",
    "jetbrains-mono": "JetBrains Mono", "instrument-serif": "Instrument Serif",
    "inter": "Inter", "archivo-black": "Archivo Black", "archivo": "Archivo",
    "fraunces": "Fraunces", "big-shoulders": "Big Shoulders", "space-grotesk": "Space Grotesk",
    "syne": "Syne", "bodoni-moda": "Bodoni Moda", "jost": "Jost", "baloo-2": "Baloo 2",
    "poppins": "Poppins", "caveat": "Caveat", "prata": "Prata", "ibm-plex-sans": "IBM Plex Sans",
    "ibm-plex-mono": "IBM Plex Mono", "dm-sans": "DM Sans", "space-mono": "Space Mono",
    "nunito": "Nunito", "unbounded": "Unbounded",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (font-fetcher)"})
    return urllib.request.urlopen(req, timeout=45).read()

def main():
    manifest = {"source": "self-hosted", "license_note": "All OFL unless noted in fonts/LICENSES.md", "faces": {}}
    for fid, weights in sorted(ROSTER_GOOGLE.items()):
        variants = ",".join(str(w) for w in weights)
        url = GW.format(id=fid, variants=variants) + "&subsets=latin,latin-ext"
        try:
            zdata = fetch(url)
            zf = zipfile.ZipFile(io.BytesIO(zdata))
            dest = FONTS / fid
            dest.mkdir(parents=True, exist_ok=True)
            files = []
            for name in zf.namelist():
                if not name.endswith(".woff2"):
                    continue
                data = zf.read(name)
                out = dest / Path(name).name
                out.write_bytes(data)
                m = re.search(r"-(\d+)", Path(name).name)  # weight in filename
                w = int(m.group(1)) if m else 400
                files.append({"file": f"fonts/{fid}/{Path(name).name}", "weight": w})
            if files:
                manifest["faces"][fid] = {"family": DISPLAY_NAME.get(fid, fid), "source": "google-gwfh", "files": files}
                print(f"ok   {fid}: {len(files)} files", flush=True)
            else:
                print(f"FAIL {fid}: no woff2 in zip", flush=True)
            time.sleep(0.4)
        except Exception as exc:
            print(f"FAIL {fid}: {exc}", flush=True)

    # fontshare — css api returns @font-face with absolute woff2 urls
    try:
        q = "&".join(f"f[]={fid}@"+",".join(str(w) for w in ws) for fid, ws in ROSTER_FONTSHARE.items())
        css = fetch(f"https://api.fontshare.com/v2/css?{q}").decode()
        for m in re.finditer(r"@font-face\s*{[^}]*font-family:\s*'([^']+)';[^}]*?font-weight:\s*(\d+);[^}]*?font-style:\s*(\w+);[^}]*?url\('([^']+\.woff2[^']*)'\)", css):
            fam, w, _style, url = m.groups()
            fid = next((k for k, v in FS_FAMILY.items() if v == fam), fam.lower())
            dest = FONTS / fid / Path(url).name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(fetch(url))
            manifest["faces"].setdefault(fid, {"family": fam, "source": "fontshare", "files": []})["files"].append(
                {"file": f"fonts/{fid}/{Path(url).name}", "weight": int(w)})
        print("ok   fontshare", flush=True)
    except Exception as exc:
        print(f"FAIL fontshare: {exc}", flush=True)

    rules = []
    for fid, face in sorted(manifest["faces"].items()):
        files = sorted(face["files"], key=lambda f: (f["weight"], f["file"]))
        files = [f for i, f in enumerate(files) if i == 0 or files[i - 1] != f]
        for f in files:
            rules.append(
                f"@font-face{{font-family:'{face['family']}';font-weight:{f['weight']};font-display:swap;"
                f"src:url({f['file']}) format('woff2');}}")
    (ROOT / "fonts.css").write_text("@layer el-fonts{" + "".join(rules) + "}\n")
    (ROOT / "fonts" / "manifest.json").write_text(json.dumps(manifest, indent=1))
    licenses = ["# Font licenses\n", "\nAll faces are delivered under their upstream licenses: SIL OFL 1.1 (Google Fonts set),\nFontshare ITF FFL (Clash Display, Satoshi, General Sans, Sentient). Source files in fonts/.\n"]
    (ROOT / "fonts" / "LICENSES.md").write_text("".join(licenses))
    total = len(manifest["faces"])
    print(f"faces={total} rules={len(rules)}", flush=True)
    return 0 if total >= 25 else 1

if __name__ == "__main__":
    sys.exit(main())