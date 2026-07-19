# Stardew Valley Mods on Steam Deck

This folder stages and manages the current Stardew Valley mod setup on the Steam Deck. Mods are installed via SMAPI into the game's `Mods/` directory.

## Prerequisites

SMAPI must be installed manually before using this tooling. Download the installer from [smapi.io](https://smapi.io) and run it on the Deck:

```bash
# On the Deck, after downloading the SMAPI Linux installer:
unzip SMAPI-*.zip
cd SMAPI\ *\ installer
./install\ on\ Linux.sh
```

SMAPI installs to `~/.local/share/Steam/steamapps/common/Stardew Valley/` and adds a Steam launch option. Verify it works before applying mods.

## Files and folders

- `mods/`: source archives — copy downloads from `nexus/downloads/` here, or place manual archives here.
- `mod-manifest.json`: ordered mod source manifest with current version, Nexus link, download link, and staged archive path.
- `install-mods.py`: installs the staged archives into `Stardew Valley/Mods/`.
- `uninstall-mods.py`: removes files from the last install manifest and restores any backed-up originals.
- `manifests/installed-files.txt`: exact list of files installed by the current mod set.
- `backups/original-files/`: original game files that were overwritten during install.
- `logs/`: install/uninstall logs.

## Stardew Valley location

Default game directory:

```bash
~/.local/share/Steam/steamapps/common/Stardew Valley
```

The scripts use this path unless `GAME_DIR` is set explicitly.

## Usage

Install the current manifest:

```bash
~/Desktop/sdv/install-mods.py
```

Uninstall the tracked files from the current mod set:

```bash
~/Desktop/sdv/uninstall-mods.py
```

Refresh the full current mod set:

```bash
~/Desktop/sdv/uninstall-mods.py
~/Desktop/sdv/install-mods.py
```

When adding a new mod later:

1. Use `nexus/info.py` to check the mod's version and requirements, and `nexus/download.py` to download it. Move the downloaded archive from `nexus/downloads/` into `mods/`.
2. Inspect its file structure. SMAPI mod archives should contain the mod folder at the root (e.g. `[CP] My Mod/`). The scripts extract into `Mods/`, so the result is `Mods/[CP] My Mod/...`.
3. Add it to the `mods` list in `mod-manifest.json` in dependency order.
4. Run `mise run apply:sdv` (uninstalls + installs on the Deck).
5. Verify `manifests/installed-files.txt`, then launch Stardew Valley and test before adding more.

## Downloading new mods

Use `nexus/download.py` to download mods — it reads Firefox cookies to authenticate with Nexus Mods.

```bash
python3 nexus/info.py "https://www.nexusmods.com/stardewvalley/mods/2400"
python3 nexus/info.py --files "https://www.nexusmods.com/stardewvalley/mods/2400"
python3 nexus/download.py "https://www.nexusmods.com/stardewvalley/mods/2400?tab=files&file_id=XXXXX"
```

Move the downloaded archive into `sdv/mods/`:

```bash
cp nexus/downloads/some-mod.zip sdv/mods/
```

Requirements:
- Firefox must be running and logged into Nexus Mods.
- The Nexus URL must include `?tab=files&file_id=NUMBER`.

## Steam Deck / Proton setup

No Proton overrides needed. Stardew Valley runs natively on Linux. SMAPI handles mod loading through its own launcher.

## Agent handoff notes

A future agent can manage this setup over SSH as the `deck` user. Key assumptions:

- SMAPI must be pre-installed on the Deck before mod scripts work.
- The source of truth for the current install is `manifests/installed-files.txt`.
- `install-mods.py` extracts archive contents into `GAME_DIR/Mods/`, preserving the internal folder structure. Archives are expected to have the mod folder at the root.
- `uninstall-mods.py` removes the full tracked mod set from the active manifest and restores any backed-up originals.
- For updates, the safest flow is: run `uninstall-mods.py`, replace archives in `mods/`, update `mod-manifest.json`, run `install-mods.py`, then launch and test.
- Dependency/framework mods should stay before content mods in the manifest. SMAPI itself is not managed by these scripts; it is a manual prerequisite.
- Legacy Bash versions of the installer/uninstaller were removed from the active folder after the Python rewrite; old copies may exist in `backups/`.
