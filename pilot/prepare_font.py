"""Download the official font and license, recording exact sources and hashes."""
from pathlib import Path
import hashlib
import json
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "fonts"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "cv-glyph-pilot/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main():
    DEST.mkdir(exist_ok=True)
    metadata = DEST / "source.json"
    if metadata.exists():
        saved = json.loads(metadata.read_text(encoding="utf-8"))
        for item in saved["files"]:
            path = DEST / item["name"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                raise RuntimeError(f"Existing resource changed: {path}")
        print("Verified existing font and license; no download needed.")
        return
    api = "https://api.github.com/repos/adobe-fonts/source-han-sans/git/ref/heads/release"
    commit = json.loads(fetch(api))["object"]["sha"]
    base = f"https://raw.githubusercontent.com/adobe-fonts/source-han-sans/{commit}"
    resources = [("SourceHanSansSC-Regular.otf", base + "/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf"),
                 ("LICENSE.txt", base + "/LICENSE.txt")]
    files = []
    for name, url in resources:
        content = fetch(url)
        if name.endswith(".otf") and content[:4] != b"OTTO":
            raise RuntimeError("Downloaded file is not an OpenType CFF font")
        if name == "LICENSE.txt" and b"SIL OPEN FONT LICENSE" not in content:
            raise RuntimeError("Unexpected license content")
        path = DEST / name
        if path.exists() and path.read_bytes() != content:
            raise RuntimeError(f"Refusing to replace different resource: {path}")
        path.write_bytes(content)
        files.append({"name": name, "url": url, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
    saved = {"repository": "https://github.com/adobe-fonts/source-han-sans", "ref": "release",
             "commit": commit, "retrieved_utc": datetime.now(timezone.utc).isoformat(), "files": files}
    metadata.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(saved, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
