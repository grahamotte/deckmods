#!/usr/bin/env python3
import os
import shutil
import sys
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


C77_DIR = Path(__file__).resolve().parent
GAME_DIR = Path(os.environ.get("GAME_DIR", Path.home() / ".local/share/Steam/steamapps/common/Cyberpunk 2077"))
BACKUP_DIR = C77_DIR / "backups/original-files"
MANIFEST_DIR = C77_DIR / "manifests"
LOG_DIR = C77_DIR / "logs"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE = LOG_DIR / f"uninstall-{STAMP}.log"
ACTIVE_MANIFEST = MANIFEST_DIR / "installed-files.txt"


def require_dir(path, message):
    if not path.is_dir():
        raise SystemExit(f"{message}: {path}")


def copy_path(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)
    else:
        shutil.copy2(source, target)


def remove_path(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        sys.stdout = Tee(original_stdout, log_file)
        sys.stderr = Tee(original_stderr, log_file)
        try:
            if not ACTIVE_MANIFEST.exists():
                print(f"No active install manifest found: {ACTIVE_MANIFEST}")
                print("Nothing to uninstall.")
                return

            require_dir(GAME_DIR, "Cyberpunk game directory not found")

            print("Uninstalling tracked Cyberpunk 2077 mods")
            print(f"Game dir: {GAME_DIR}")
            print(f"Installed files: {ACTIVE_MANIFEST}")
            print(f"Log:      {LOG_FILE}")
            print()

            installed_files = [line.strip() for line in ACTIVE_MANIFEST.read_text(encoding="utf-8").splitlines()]
            for relpath in sorted((path for path in installed_files if path), reverse=True):
                target = GAME_DIR / relpath
                backup = BACKUP_DIR / relpath

                if backup.exists():
                    copy_path(backup, target)
                    print(f"  restored original {relpath}")
                elif target.exists():
                    remove_path(target)
                    print(f"  removed {relpath}")

            archived_manifest = MANIFEST_DIR / f"installed-files-uninstalled-{STAMP}.txt"
            ACTIVE_MANIFEST.replace(archived_manifest)

            print()
            print(f"Done. Previous manifest archived in {MANIFEST_DIR}.")
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr


if __name__ == "__main__":
    main()
