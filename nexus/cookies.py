import hashlib
import http.cookiejar
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ARC_COOKIES = Path.home() / "Library/Application Support/Arc/User Data/Default/Cookies"


def load_cookies():
    if not ARC_COOKIES.exists():
        raise SystemExit("No Arc cookie database found")

    password = subprocess.run(
        ["security", "find-generic-password", "-s", "Arc Safe Storage", "-w"],
        check=True, capture_output=True,
    ).stdout.strip()
    key = hashlib.pbkdf2_hmac("sha1", password, b"saltysalt", 1003, 16).hex()

    with tempfile.NamedTemporaryFile() as tmp:
        shutil.copy2(ARC_COOKIES, tmp.name)
        conn = sqlite3.connect(f"file:{tmp.name}?mode=ro", uri=True)
        rows = conn.execute(
            "SELECT name, encrypted_value, host_key, path, is_secure "
            "FROM cookies WHERE host_key LIKE '%nexus%'"
        ).fetchall()
        conn.close()

    jar = http.cookiejar.CookieJar()
    for name, encrypted, host, path, is_secure in rows:
        if not encrypted.startswith(b"v10"):
            continue
        value = subprocess.run(
            ["openssl", "enc", "-d", "-aes-128-cbc", "-K", key, "-iv", "20" * 16],
            input=encrypted[3:], check=True, capture_output=True,
        ).stdout
        host_hash = hashlib.sha256(host.encode()).digest()
        if value.startswith(host_hash):
            value = value[len(host_hash):]
        value = value.decode()
        jar.set_cookie(http.cookiejar.Cookie(
            version=0, name=name, value=value, port=None, port_specified=False,
            domain=host, domain_specified=True, domain_initial_dot=host.startswith("."),
            path=path, path_specified=True, secure=bool(is_secure), expires=None,
            discard=False, comment=None, comment_url=None, rest={}, rfc2109=False,
        ))
    return jar
