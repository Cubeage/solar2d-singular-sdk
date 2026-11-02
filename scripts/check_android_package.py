#!/usr/bin/env python3
"""Check the published Solar2D Android package without extracting its contents."""

import io
from pathlib import Path
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = {"plugin-release.aar", "corona.gradle", "metadata.lua"}
ENTRY_POINT = "plugin/singular/LuaLoader.class"


def check_package(path, source_root=ROOT):
    with tarfile.open(path, "r:gz") as package:
        files = {}
        for member in package.getmembers():
            # tar -C package_android . includes a root directory and ./ prefixes.
            name = member.name.removeprefix("./")
            if member.isdir() and name in ("", "."):
                continue
            if not member.isfile() or name not in FILES or name in files:
                raise ValueError(f"Unexpected or duplicate package member: {member.name}")
            files[name] = package.extractfile(member).read()
        if files.keys() != FILES:
            raise ValueError(f"Missing package files: {FILES - files.keys()}")

    for name, source in (("metadata.lua", "metadata.lua"),
                         ("corona.gradle", "android/corona.gradle")):
        if files[name] != (source_root / source).read_bytes():
            raise ValueError(f"Packaged {name} differs from the checked-out source")

    with zipfile.ZipFile(io.BytesIO(files["plugin-release.aar"])) as aar:
        if "AndroidManifest.xml" not in aar.namelist():
            raise ValueError("AAR has no AndroidManifest.xml")
        with zipfile.ZipFile(io.BytesIO(aar.read("classes.jar"))) as classes:
            if not classes.read(ENTRY_POINT).startswith(b"\xca\xfe\xba\xbe"):
                raise ValueError("Missing or invalid plugin.singular.LuaLoader bytecode")
            if any(name.startswith(("com/ansca/", "com/naef/", "com/singular/"))
                   for name in classes.namelist()):
                raise ValueError("AAR must not bundle consumer-provided runtime classes")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check_android_package.py android.tgz")
    check_package(sys.argv[1])
    print("Android package smoke passed: plugin entry point, manifest and source metadata")


if __name__ == "__main__":
    main()
