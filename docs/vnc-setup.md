# Steam Deck VNC Setup

This Deck is configured for Mac Screen Sharing using KDE Desktop Sharing (`krfb`).

## How to connect

From macOS Finder:

1. Choose **Go > Connect to Server...**
2. Enter `vnc://192.168.1.239:5900`
3. Use password: `********`

The service listens on TCP port `5900`, the standard VNC port.

## How it starts

The active setup is a user systemd service:

- Service file: `~/.config/systemd/user/krfb.service`
- Command: `/usr/bin/krfb --nodialog`
- Enabled for: `graphical-session.target`

That means it starts when the Deck enters KDE Plasma Desktop Mode, not while only Gaming Mode is running.

Useful commands:

```bash
systemctl --user status krfb.service
systemctl --user restart krfb.service
systemctl --user stop krfb.service
systemctl --user start krfb.service
journalctl --user -u krfb.service -n 100 --no-pager
```

## Config

KRFB settings are stored in:

- `~/.config/krfbrc`

Important settings:

- `preferredFrameBufferPlugin=pw` uses KDE/Wayland/PipeWire screen capture.
- `allowUnattendedAccess=true` allows login without approving a popup on the Deck.
- `allowDesktopControl=true` allows remote keyboard and mouse control.
- `port=5900` fixes the VNC port for Mac Screen Sharing.
- `noWallet=true` keeps the VNC password in KRFB config instead of depending on KWallet being unlocked.

Note: VNC password handling in some clients/servers historically only uses the first 8 characters. The configured password is `paranoidtuna`; if a very old VNC client behaves oddly, that protocol limit is the likely reason.

## Old setup

The old `x11vnc` Desktop launchers were moved to:

- `~/Desktop/old/legacy-x11vnc-launchers/`

Those launchers used `x11vnc -display :0`, which is brittle on current Steam Deck Desktop Mode because Plasma runs on Wayland with Xwayland. The current setup uses KDE's own Desktop Sharing app instead.

I checked for old VNC-related systemd services and KDE autostart entries. The only enabled VNC-related service is the current `krfb.service`.

## SteamOS update note

SteamOS has a read-only system image. The `krfb` package was installed from the SteamOS package repo, so a major SteamOS update may remove it. If VNC stops working after an update, check:

```bash
command -v krfb
systemctl --user status krfb.service
```

If `krfb` is missing, reinstall it with the SteamOS package manager, then restart `krfb.service`.
