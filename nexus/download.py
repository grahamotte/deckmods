#!/usr/bin/env python3
"""Download a file from Nexus Mods using Arc cookies.

Usage:
  download.py <nexus-file-url>
  download.py --game-id N --file-id N <nexus-file-url>

Example:
  download.py "https://www.nexusmods.com/cyberpunk2077/mods/2380?tab=files&file_id=139049"
"""
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from cookies import load_cookies

SCRIPT_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"


def parse_url(url):
    m = re.search(r"nexusmods\.com/([^/]+)/mods/(\d+)", url)
    if not m:
        raise SystemExit(f"Cannot parse Nexus Mods URL: {url}")
    game_name = m.group(1)
    mod_id = int(m.group(2))
    params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    file_ids = params.get("file_id", [])
    if not file_ids:
        raise SystemExit("URL must include ?tab=files&file_id=NUMBER")
    return game_name, mod_id, int(file_ids[0])


def fetch_game_id(cookies, game_name, mod_id):
    url = f"https://www.nexusmods.com/{game_name}/mods/{mod_id}?tab=description"
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    resp = opener.open(req)
    body = resp.read().decode("utf-8", errors="replace")
    m = re.search(r'data-game-id="(\d+)"', body)
    if not m:
        raise SystemExit("Could not find game_id on mod page")
    return int(m.group(1))


def get_download_url(cookies, game_id, file_id):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    body = urllib.parse.urlencode({
        "game_id": str(game_id),
        "fid": str(file_id),
        "collection_id": "0",
    }).encode()

    req = urllib.request.Request(
        "https://www.nexusmods.com/Core/Libs/Common/Managers/Downloads?GenerateDownloadUrl",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": UA,
            "Referer": "https://www.nexusmods.com/",
            "Origin": "https://www.nexusmods.com",
        },
    )

    resp = opener.open(req)
    data = json.loads(resp.read().decode("utf-8", errors="replace"))
    url = data.get("url")
    if not url:
        raise SystemExit(f"No download URL in response: {data}")
    return url


def download(cookies, url, dest):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    resp = opener.open(req)

    total = resp.headers.get("Content-Length")
    total = int(total) if total else None

    dest.parent.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    with open(dest, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded * 100 // total
                mb_dl = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                print(f"\r  {pct}%  {mb_dl:.1f}/{mb_total:.1f} MB", end="", flush=True)
    if total:
        print()
    print(f"Saved: {dest.name}")


def main():
    args = sys.argv[1:]
    game_id = None
    file_id = None
    url = None

    i = 0
    while i < len(args):
        if args[i] == "--game-id":
            i += 1; game_id = int(args[i])
        elif args[i] == "--file-id":
            i += 1; file_id = int(args[i])
        elif not url:
            url = args[i]
        else:
            raise SystemExit(f"Unexpected argument: {args[i]}")
        i += 1

    if not url:
        raise SystemExit(
            "Usage: download.py <nexus-file-url>\n"
            "       download.py --game-id N --file-id N <nexus-file-url>\n"
        )

    print("Loading Arc cookies ...")
    cookies = load_cookies()

    game_name, mod_id, parsed_file_id = parse_url(url)
    if not file_id:
        file_id = parsed_file_id

    if not game_id:
        print(f"Fetching game_id for {game_name} ...")
        game_id = fetch_game_id(cookies, game_name, mod_id)
        print(f"  game_id = {game_id}")

    print(f"Getting download URL for mod {mod_id}, file {file_id} ...")
    dl_url = get_download_url(cookies, game_id, file_id)

    filename = Path(urllib.parse.unquote(urllib.parse.urlparse(dl_url).path)).name
    dest = DOWNLOADS_DIR / filename

    if dest.exists():
        print(f"Already downloaded: {filename}")
        return

    download(cookies, dl_url, dest)


if __name__ == "__main__":
    main()
