#!/usr/bin/env python3
"""Show info about a Nexus Mods mod (name, version, requirements, files).

Usage:
  info.py <nexus-mod-url>
  info.py --files <nexus-mod-url>   # also list available files

Examples:
  info.py https://www.nexusmods.com/cyberpunk2077/mods/7780
  info.py --files https://www.nexusmods.com/cyberpunk2077/mods/2380
"""
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from cookies import load_cookies

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"


def fetch(cookies, url, referer=None):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    resp = opener.open(req)
    return resp.read().decode("utf-8", errors="replace")


def parse_mod_info(html, mod_url):
    info = {}

    # Title -> mod name
    m = re.search(r"<title>([^<]+)</title>", html)
    if m:
        title = m.group(1)
        name = title.split(" at ")[0].strip()
        info["name"] = name

    # Version from twitter meta tag
    m = re.search(r'<meta\s+property="twitter:data1"\s+content="([^"]+)"', html)
    if m:
        info["version"] = m.group(1)

    # Game ID
    m = re.search(r'data-game-id="(\d+)"', html)
    if m:
        info["game_id"] = int(m.group(1))

    # Mod ID from URL
    m = re.search(r"/mods/(\d+)", mod_url)
    if m:
        info["mod_id"] = int(m.group(1))

    # Requirements - parse the accordion section
    reqs = []
    req_section_start = html.find('data-accordion-track="mod_requirements"')
    if req_section_start >= 0:
        req_section = html[req_section_start:]
        req_section_end = req_section.find("</dd>")
        if req_section_end >= 0:
            req_section = req_section[:req_section_end]

        for m in re.finditer(
            r'<a\s[^>]*href="(https://www\.nexusmods\.com/[^/]+/mods/\d+)"[^>]*>\s*([^<]+)\s*</a>',
            req_section,
        ):
            reqs.append({"name": m.group(2).strip(), "url": m.group(1)})

    info["requirements"] = reqs
    return info


def parse_files(html):
    """Parse file entries from the files tab or description page."""
    files = []

    # Files in the mod-file-download web component or file table
    # Look for file entries in the HTML
    for m in re.finditer(
        r'<(?:a|mod-file-download)\s[^>]*'
        r'(?:href="([^"]*(?:file_id=(\d+))[^"]*)"|file-id="(\d+)")'
        r'[^>]*>',
        html,
    ):
        file_url = m.group(1)
        file_id = m.group(2) or m.group(3)
        if file_id and file_url:
            files.append({"file_id": int(file_id), "url": file_url})
        elif file_id:
            files.append({"file_id": int(file_id)})

    return files


def parse_files_from_tab(html):
    """Parse files from the files tab page using data attributes on dt elements."""
    files = []

    for m in re.finditer(r'<dt\s[^>]*?\bclass="file-expander-header[^"]*"[^>]*?data-id="(\d+)"[^>]*?>', html):
        attrs = m.group(0)
        entry = {"file_id": int(m.group(1))}

        name = re.search(r'data-name="([^"]*)"', attrs)
        if name:
            entry["name"] = name.group(1)

        version = re.search(r'data-version="([^"]*)"', attrs)
        if version:
            entry["version"] = version.group(1)

        size = re.search(r'data-size="([^"]*)"', attrs)
        if size:
            entry["size_kb"] = size.group(1)

        deps = re.search(r'data-dependencies-count="([^"]*)"', attrs)
        if deps:
            entry["deps"] = deps.group(1)

        files.append(entry)

    return files


def main():
    args = sys.argv[1:]
    show_files = False

    if not args:
        raise SystemExit("Usage: info.py [--files] <nexus-mod-url>")

    pos_args = []
    for a in args:
        if a == "--files":
            show_files = True
        else:
            pos_args.append(a)

    mod_url = pos_args[0]
    if "nexusmods.com" not in mod_url:
        raise SystemExit("Expected a Nexus Mods URL")

    print("Loading Arc cookies ...")
    cookies = load_cookies()

    print(f"Fetching mod info ...")
    html = fetch(cookies, mod_url)
    info = parse_mod_info(html, mod_url)

    print(f"Name:       {info.get('name', '?')}")
    print(f"Version:    {info.get('version', '?')}")
    print(f"Mod ID:     {info.get('mod_id', '?')}")
    print(f"Game ID:    {info.get('game_id', '?')}")

    reqs = info.get("requirements", [])
    print(f"Required:   {len(reqs)} mod(s)")
    for r in reqs:
        print(f"  - {r['name']}")
        print(f"    {r['url']}")

    if show_files:
        print()
        print(f"Fetching file list ...")
        game_name_match = re.search(r"nexusmods\.com/([^/]+)/mods/", mod_url)
        game_name = game_name_match.group(1) if game_name_match else "cyberpunk2077"
        mod_id = info.get("mod_id", "")

        files_url = f"https://www.nexusmods.com/{game_name}/mods/{mod_id}?tab=files"
        html = fetch(cookies, files_url, referer=mod_url)
        files = parse_files_from_tab(html)

        print(f"Files:      {len(files)} file(s)")
        for f in files:
            fid = f.get("file_id", "?")
            fname = f.get("name", "?")
            fsize = f.get("size_kb", "?")
            if fsize != "?":
                try:
                    kb = int(fsize)
                    fsize = f"{kb / 1024:.1f}MB" if kb >= 1024 else f"{kb}KB"
                except ValueError:
                    pass
            fver = f.get("version", "")
            fn = fname if not fname.endswith((".zip", ".7z", ".rar")) else fname
            print(f"  file_id={fid}  {fver:10s}  {fsize:>8s}  {fn}")

    if reqs:
        print()
        print("To download requirements:")
        for r in reqs:
            print(f"  # {r['name']} — open the mod page and pick a file_id, then:")
            print(f'  python3 nexus/download.py "{r["url"]}?tab=files&file_id=XXX"')


if __name__ == "__main__":
    main()
