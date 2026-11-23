"""Index ZIP releases uploaded to packages/ without executing their contents."""
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

root = Path(__file__).resolve().parent
index_path = root / "vyrclad-index.json"
previous = json.loads(index_path.read_bytes())["plugins"] if index_path.exists() else []
published = {(r["id"], r["version"]): r["sha256"] for r in previous}
releases = []
source_packages = set()
packages = root / "packages"
packages.mkdir(exist_ok=True)
for manifest in sorted((root / "plugin").glob("*/*/info.json")):
    folder = manifest.parent
    info = json.loads(manifest.read_bytes())
    if (info["module"], info["name"]) != (folder.parent.name, folder.name):
        raise ValueError(f"Module or name differs from its source directory: {folder}")
    identity = (info["module"] + "." + info["name"]).lower()
    parts = info["version"].removeprefix("v").split(".")
    version = ".".join(parts + ["0"] * (3-len(parts)))
    if not re.fullmatch(r"[a-z][a-z0-9._-]{0,79}", identity) or not re.fullmatch(r"[0-9]{1,9}(?:\.[0-9]{1,9}){2}", version):
        raise ValueError(f"Invalid source name or version: {folder}")
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        for name in ("info.json", "plugin.go"):
            item = folder / name
            if item.is_symlink() or item.stat().st_size > (64 << 10 if name == "info.json" else 256 << 10):
                raise ValueError(f"Invalid plugin source: {item}")
            # Stored entries give identical release bytes on Windows and Linux.
            entry = zipfile.ZipInfo(name)
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, item.read_bytes().replace(b"\r\n", b"\n"))
    out = packages / (identity + "@" + version + ".zip")
    if out.exists() and out.read_bytes() != data.getvalue():
        raise ValueError(f"Source changed for {out.name}. Publish a new version.")
    out.write_bytes(data.getvalue())
    source_packages.add(out.name)
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
    release = {"id": identity, "version": version, "format": "zip", "sha256": digest}
    if path.name in source_packages:
        release["hasSource"] = True
    with zipfile.ZipFile(path) as archive:
        if "plugin.go" in archive.namelist() and "info.json" in archive.namelist() and archive.getinfo("info.json").file_size <= 64 << 10:
            try:
                info = json.loads(archive.read("info.json"))
            except (ValueError, UnicodeError):
                info = None
            if isinstance(info, dict):
                for key in ("name", "module", "introduction"):
                    if isinstance(info.get(key), str):
                        release[key] = info[key]
    releases.append(release)

encoded = (json.dumps({"schema": "vyrclad.plugins/v1", "plugins": releases}, indent=2) + "\n").encode()
if len(encoded) > 256 << 10:
    raise ValueError("Index exceeds 256 KiB")
index_path.write_bytes(encoded)
