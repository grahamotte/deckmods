# Cyberpunk 2077 Mods on Steam Deck

This folder stages and manages the current Cyberpunk 2077 mod setup on the Steam Deck.

## Current mod set

Install order and source metadata are encoded in `mod-manifest.json`; `install-mods.py` reads that file. The current manifest has 19 mod entries and the latest verified install tracks 177 files in `manifests/installed-files.txt`.

The framework/dependency mods are installed before gameplay/content mods. Better Vehicle Handling was removed after testing because it did not feel right in game; its repacked archive is stored under `removed-mods/` instead of active `mods/`.

## Files and folders

- `mods/`: source archives — copy downloads from `nexus/downloads/` here, or place manual archives here.
- `mod-manifest.json`: ordered mod source manifest with current version, Nexus link, download link, and staged archive path.
- `install-mods.py`: installs the staged archives into the Cyberpunk game directory.
- `uninstall-mods.py`: removes files from the last install manifest and restores any backed-up originals.
- `manifests/installed-files.txt`: exact list of files installed by the current mod set.
- `backups/original-files/`: original game files that were overwritten during install.
- `backups/`: snapshots of scripts/manifests from previous update cycles.
- `logs/`: install/uninstall logs.

## Cyberpunk location

Default game directory:

```bash
~/.local/share/Steam/steamapps/common/Cyberpunk 2077
```

The scripts use this path unless `GAME_DIR` is set explicitly.

## Steam Deck / Proton setup

Protontricks was used for Cyberpunk app id `1091500` to install:

- `d3dcompiler_47`
- `vcrun2022`

Cyberpunk Steam launch options were set to:

```bash
WINEDLLOVERRIDES="winmm,version=n,b" %command%
```

That override is needed so Proton loads RED4ext/Cyberpunk mod framework DLLs correctly.

## Usage

Install the current manifest:

```bash
~/Desktop/c77/install-mods.py
```

Uninstall the tracked files from the current mod set:

```bash
~/Desktop/c77/uninstall-mods.py
```

Refresh the full current mod set:

```bash
~/Desktop/c77/uninstall-mods.py
~/Desktop/c77/install-mods.py
```

When adding a new mod later:

1. Use `nexus/info.py` to check the mod's version and requirements, and `nexus/download.py` to download it. Move the downloaded archive from `nexus/downloads/` into `mods/`.
2. For grouped submods, place archives under a subfolder like `mods/proxima-apartment-emporium/`.
3. Inspect its file structure and requirements. Archives should contain game-root-relative paths such as `archive`, `bin`, `engine`, `r6`, or `red4ext`.
4. Add it to the `mods` list in `mod-manifest.json` in dependency order. Use a `download_path` relative to `mods/` for grouped archives, for example `proxima-apartment-emporium/Some Preset.7z`.
5. Run `mise run apply:c77` (uninstalls + installs on the Deck).
6. Verify `manifests/installed-files.txt`, then launch Cyberpunk and test before adding more.

## Downloading new mods

Use `nexus/download.py` to download mods — it reads Arc cookies to authenticate with Nexus Mods (same approach as gallery-dl/yt-dlp `--cookies-from-browser`). No manual download or browser interaction needed.

First, check the mod page:

```bash
python3 nexus/info.py "https://www.nexusmods.com/cyberpunk2077/mods/2380"
python3 nexus/info.py --files "https://www.nexusmods.com/cyberpunk2077/mods/2380"  # also list available files
```

Then download the correct file:

```bash
python3 nexus/download.py "https://www.nexusmods.com/cyberpunk2077/mods/2380?tab=files&file_id=139049"
```

Move the downloaded archive into `c77/mods/`:

```bash
cp nexus/downloads/RED4ext-2380-1-30-0-1773082858.zip c77/mods/
```

Requirements:
- Arc must be logged into Nexus Mods (`nexusmods_session` cookie must be present).
- The Nexus URL must include `?tab=files&file_id=NUMBER`.
- If a mod page has multiple file entries (main, optional, old versions, translations), use `--files` to list them and pick the right one. Do not guess.

## REDmod note

This setup does not currently use REDmod. These are legacy/framework-style mods that merge directly into the game directory. REDmod is only needed for mods that explicitly say REDmod-only.

## Agent handoff notes

A future agent can manage this setup over SSH as the `deck` user. Key assumptions:

- The source of truth for the current install is `manifests/installed-files.txt`.
- `install-mods.py` installs every archive listed in `mod-manifest.json`; it is not currently a per-mod installer.
- `uninstall-mods.py` removes the full tracked mod set from the active manifest. It is not currently a selective per-mod uninstaller, and it intentionally leaves empty folders alone.
- Before replacing or removing a mod, copy the current `manifests/installed-files.txt`, `mod-manifest.json`, scripts, and relevant logs for reference.
- For updates, the safest flow is: run `uninstall-mods.py`, replace archives in `mods/`, update `mod-manifest.json`, run `install-mods.py`, then launch and test.
- Dependency/framework archives should stay before content mods. Current dependency order is RED4ext, Cyber Engine Tweaks, redscript, ArchiveXL, TweakXL, Codeware, and Input Loader before gameplay/content mods.
- For a new mod, inspect the archive contents first. Archives that already contain top-level folders such as `archive`, `bin`, `engine`, `r6`, or `red4ext` can usually be merged into the game root. REDmod-style mods with `info.json` under a mod folder need a separate REDmod flow and are not covered by these scripts yet.
- Keep Steam launch options set to `WINEDLLOVERRIDES="winmm,version=n,b" %command%` for RED4ext/framework loading under Proton.
- After game updates, expect RED4ext/redscript/ArchiveXL/TweakXL/Codeware to need updates before content mods work reliably.
- Legacy Bash versions of the installer/uninstaller were removed from the active folder after the Python rewrite; old copies may exist in `backups/`.

Useful verification commands:

```bash
wc -l ~/Desktop/c77/manifests/installed-files.txt
python3 -m json.tool ~/Desktop/c77/mod-manifest.json >/dev/null
ls ~/.local/share/Steam/steamapps/common/'Cyberpunk 2077'/red4ext/RED4ext.dll
ls ~/.local/share/Steam/steamapps/common/'Cyberpunk 2077'/bin/x64/plugins/cyber_engine_tweaks/mods/AppearanceMenuMod/init.lua
ls ~/.local/share/Steam/steamapps/common/'Cyberpunk 2077'/archive/pc/mod/NightCityInteractions.archive
```
