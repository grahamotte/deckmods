# Deckmods Agent Notes

Keep changes small. This repo manages Steam Deck mod tooling, not the live game install.

Steam Deck target:

- Host: `deck@192.168.1.239`
- Cyberpunk staging folder: `~/Desktop/c77`
- Game folder: `~/.local/share/Steam/steamapps/common/Cyberpunk 2077`
- Stardew Valley staging folder: `~/Desktop/sdv`
- Game folder: `~/.local/share/Steam/steamapps/common/Stardew Valley`

Repo shape:

- `c77/` mirrors the active Cyberpunk management files on the Deck desktop.
- `sdv/` mirrors the active Stardew Valley management files on the Deck desktop.
- `c77/mods/` and `sdv/mods/` contain downloaded archives and are intentionally ignored.
- `nexus/` is a self-contained Nexus Mods downloader that reads Firefox cookies.
  - `nexus/info.py` — shows mod name, version, requirements, and files.
  - `nexus/download.py` — downloads a specific file by `file_id`.
  - `nexus/downloads/` — where downloaded archives land (gitignored).
- Deck-only runtime state stays off git: `backups/`, `logs/`, `manifests/`, `removed-mods/`, `__pycache__/`.

Nexus Mods workflow:

1. Use `nexus/info.py` to check a mod's version and requirements:
   ```bash
   python3 nexus/info.py "https://www.nexusmods.com/cyberpunk2077/mods/7780"
   python3 nexus/info.py --files "https://www.nexusmods.com/cyberpunk2077/mods/7780"  # also list files
   ```
2. Download the correct file with `nexus/download.py`:
   ```bash
   python3 nexus/download.py "https://www.nexusmods.com/cyberpunk2077/mods/7780?tab=files&file_id=144164"
   ```
3. Move the downloaded archive from `nexus/downloads/` into `c77/mods/`.
4. Update `c77/mod-manifest.json`, then run `mise run apply:c77`.

If a mod page has multiple files (main, optional, old versions, translations), ask before downloading — do not guess. Use `--files` to list them first. When the correct file is obvious (single main file, latest version), download it without asking.

Common commands:

```bash
mise run apply       # push managed tooling to the Deck and apply mods
mise run apply:c77   # push c77 tooling to the Deck and apply c77 mods
mise run apply:sdv   # push sdv tooling to the Deck and apply sdv mods
mise run unapply     # remove managed mods from the Deck
mise run unapply:c77
mise run unapply:sdv
```

Debugging example:

```bash
ssh deck@192.168.1.239 'ls -la ~/Desktop/c77'
```

Do not use `--dry-run` in this repo.
Run install/uninstall flows through mise. Raw SSH is fine for debugging and inspection.

When changing mods, follow the add-mod process in `c77/README.md` or `sdv/README.md`, update the appropriate `mod-manifest.json` and scripts locally, then run the relevant mise task. Treat local git as the source of truth; do not pull generated Deck state back into the repo.

Stardew Valley mods install into `Mods/` inside the game directory (not merged into the game root like Cyberpunk). SMAPI is a manual prerequisite — it is not managed by these scripts.
