"""Index ZIP releases uploaded to packages/ without executing their contents."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

root = Path(__file__).resolve().parent
index_path = root / "vyrclad-index.json"
previous = json.loads(index_path.read_bytes())["plugins"] if index_path.exists() else []
published = {(r["id"], r["version"]): r["sha256"] for r in previous}
releases = []
for path in sorted((root / "packages").glob("*.zip")):
    match = re.fullmatch(r"([a-z][a-z0-9._-]{0,79})@([0-9]{1,9}(?:\.[0-9]{1,9}){2})\.zip", path.name)
    if not match or path.stat().st_size > 32 << 20:
        raise ValueError(f"Invalid package filename or size: {path.name}")
    identity, version = match.groups()
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 4096 or not any(not f.is_dir() for f in entries) or sum(f.file_size for f in entries) > 128 << 20:
            raise ValueError(f"Invalid archive size or entry count: {path.name}")
        if archive.testzip() is not None:
            raise ValueError(f"Corrupt archive: {path.name}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if (identity, version) in published and published[identity, version] != digest:
        raise ValueError(f"Already published with different contents: {path.name}. Use a new version.")
    releases.append({"id": identity, "version": version, "format": "zip", "sha256": digest})

encoded = (json.dumps({"schema": "vyrclad.plugins/v1", "plugins": releases}, indent=2) + "\n").encode()
if len(encoded) > 256 << 10:
    raise ValueError("Index exceeds 256 KiB")
index_path.write_bytes(encoded)
