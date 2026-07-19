#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


SDV_DIR = Path(__file__).resolve().parent
GAME_DIR = Path(os.environ.get("GAME_DIR", Path.home() / ".local/share/Steam/steamapps/common/Stardew Valley"))
MODS_DIR = SDV_DIR / "mods"
MOD_MANIFEST = SDV_DIR / "mod-manifest.json"
BACKUP_DIR = SDV_DIR / "backups/original-files"
MANIFEST_DIR = SDV_DIR / "manifests"
LOG_DIR = SDV_DIR / "logs"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE = LOG_DIR / f"install-{STAMP}.log"
ACTIVE_MANIFEST = MANIFEST_DIR / "installed-files.txt"


def require_file(path):
    if not path.is_file():
        raise SystemExit(f"Missing required file: {path}")


def require_dir(path, message):
    if not path.is_dir():
        raise SystemExit(f"{message}: {path}")


def should_skip(relpath):
    if not relpath or relpath.endswith("/"):
        return True
    parts = Path(relpath).parts
    return relpath == ".DS_Store" or "__MACOSX" in parts or ".DS_Store" in parts


def copy_path(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)
    else:
        shutil.copy2(source, target)


def list_archive(archive_path):
    result = subprocess.run(
        ["bsdtar", "-tf", str(archive_path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.splitlines()


def extract_archive(archive_path, extract_dir):
    subprocess.run(["bsdtar", "-xf", str(archive_path), "-C", str(extract_dir)], check=True)


def load_manifest():
    import json

    require_file(MOD_MANIFEST)
    with MOD_MANIFEST.open(encoding="utf-8") as file:
        manifest = json.load(file)

    mods = manifest.get("mods", [])
    if not mods:
        raise SystemExit(f"No mods listed in {MOD_MANIFEST}")

    required_fields = ("name", "current_version", "download_path")
    for index, mod in enumerate(mods, start=1):
        for field in required_fields:
            if not mod.get(field):
                raise SystemExit(f"Missing {field} for mod #{index}: {mod}")

    return manifest


def ensure_smapi(game_dir):
    smapi_binary = game_dir / "StardewModdingAPI"
    if smapi_binary.exists():
        print("SMAPI is already installed.")
        return

    raise SystemExit(
        "SMAPI is not installed. Install it first:\n"
        "  1. Download SMAPI from https://smapi.io\n"
        "  2. Extract and run 'install on Linux.sh' on the Deck\n"
        "  3. Configure the Steam launch option as prompted\n"
        "Then run apply again.\n"
    )


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        sys.stdout = Tee(original_stdout, log_file)
        sys.stderr = Tee(original_stderr, log_file)
        try:
            manifest = load_manifest()
            require_dir(GAME_DIR, "Stardew Valley game directory not found")

            # Verify the game binary exists
            game_binary = GAME_DIR / "Stardew Valley"
            if not game_binary.exists():
                raise SystemExit(f"Stardew Valley binary not found in {GAME_DIR}")

            ensure_smapi(GAME_DIR)

            target_base = GAME_DIR / "Mods"

            if ACTIVE_MANIFEST.exists():
                shutil.copy2(ACTIVE_MANIFEST, MANIFEST_DIR / f"installed-files-before-{STAMP}.txt")

            installed_files = set()

            print("Installing Stardew Valley mods")
            print(f"Game dir:    {GAME_DIR}")
            print(f"Mod target:  {target_base}")
            print(f"Mod dir:     {MODS_DIR}")
            print(f"Manifest:    {MOD_MANIFEST}")
            print(f"Log:         {LOG_FILE}")
            print()

            for mod in manifest["mods"]:
                archive = mod["download_path"]
                archive_path = MODS_DIR / archive
                require_file(archive_path)

                print(f"==> Installing {mod['name']} {mod['current_version']}")
                print(f"    {archive}")

                relpaths = list_archive(archive_path)
                with tempfile.TemporaryDirectory() as extract_dir_name:
                    extract_dir = Path(extract_dir_name)
                    extract_archive(archive_path, extract_dir)

                    for relpath in relpaths:
                        if should_skip(relpath):
                            continue

                        source = extract_dir / relpath
                        if not source.is_file():
                            continue

                        target = target_base / relpath
                        backup = BACKUP_DIR / relpath

                        if target.exists() and not backup.exists():
                            copy_path(target, backup)
                            print(f"  backed up existing {relpath}")

                        copy_path(source, target)
                        installed_files.add(relpath)

            tmp_manifest = ACTIVE_MANIFEST.with_suffix(".txt.tmp")
            tmp_manifest.write_text("".join(f"{path}\n" for path in sorted(installed_files)), encoding="utf-8")
            tmp_manifest.replace(ACTIVE_MANIFEST)

            print()
            print(f"Installed {len(installed_files)} tracked files.")
            print(f"Backups for overwritten files are in: {BACKUP_DIR}")
            print("Done.")
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr


if __name__ == "__main__":
    main()
