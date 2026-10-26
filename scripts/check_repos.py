#!/usr/bin/env python3
"""Daily health check for the repos in repos.json.

Writes two files next to repos.json:
  status.json  public, read by the web page: status, package count, last real update
  state.json   private bookkeeping: package versions, ETags, consecutive failures

A repo counts as "updated" only when a package is added or a version changes,
so a maintainer regenerating Release files does not look like activity.
Standard library only; zstd-compressed indexes are read if `zstandard` is installed.
"""
import bz2
import email.utils
import gzip
import hashlib
import json
import lzma
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOS = ROOT / "repos.json"
STATUS = ROOT / "status.json"
STATE = ROOT / "state.json"

HEADERS = {
    "User-Agent": "Sileo/2.5.1 CoreFoundation/1.0 Darwin/23.0.0",
    "X-Firmware": "17.0",
    "X-Machine": "iPhone15,2",
    "Accept-Encoding": "identity",
}
TIMEOUT = 15
DEAD_AFTER = 3  # consecutive failed days before a repo is shown as dead


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get(url, extra=None):
    req = urllib.request.Request(url, headers={**HEADERS, **(extra or {})})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read(), r.headers
    except urllib.error.HTTPError as e:
        return e.code, b"", e.headers


def decompress(name, data):
    if name.endswith(".xz"):
        return lzma.decompress(data)
    if name.endswith(".bz2"):
        return bz2.decompress(data)
    if name.endswith(".gz"):
        return gzip.decompress(data)
    if name.endswith(".zst"):
        import zstandard  # optional
        return zstandard.ZstdDecompressor().decompressobj().decompress(data)
    return data


def parse_packages(text):
    """Return {package: highest-seen version string}."""
    out = {}
    for block in text.split("\n\n"):
        pkg = ver = None
        for line in block.splitlines():
            if line.startswith("Package:"):
                pkg = line.split(":", 1)[1].strip()
            elif line.startswith("Version:"):
                ver = line.split(":", 1)[1].strip()
        if pkg:
            out.setdefault(pkg, set()).add(ver or "")
    return {p: sorted(v)[-1] for p, v in out.items()}


def release_date(text):
    for line in text.splitlines():
        if line.startswith("Date:"):
            try:
                return email.utils.parsedate_to_datetime(line[5:].strip()).astimezone(timezone.utc).isoformat()
            except (TypeError, ValueError):
                return None
    return None


def http_date(headers):
    lm = headers.get("Last-Modified") if headers else None
    if not lm:
        return None
    try:
        return email.utils.parsedate_to_datetime(lm).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def check(url, prev):
    base = url if url.endswith("/") else url + "/"
    result = {"ok": False}

    code, body, release_headers = get(base + "Release")
    if code != 200 or b"Origin" not in body and b"Label" not in body and b"Suite" not in body:
        result["error"] = f"Release HTTP {code}"
        return result
    rel_text = body.decode("utf-8", "replace")

    cond = {}
    if prev.get("etag"):
        cond["If-None-Match"] = prev["etag"]
    for name in ("Packages.xz", "Packages.bz2", "Packages.gz", "Packages.zst", "Packages"):
        code, data, headers = get(base + name, cond if name == prev.get("index") else None)
        if code == 304:
            return {"ok": True, "unchanged": True, "index": name, "etag": prev.get("etag"),
                    "seed_date": release_date(rel_text) or http_date(release_headers)}
        if code != 200 or not data:
            continue
        try:
            text = decompress(name, data).decode("utf-8", "replace")
        except Exception:
            continue
        if "Package:" not in text:
            continue
        return {
            "ok": True,
            "index": name,
            "etag": headers.get("ETag"),
            "versions": parse_packages(text),
            "seed_date": release_date(rel_text) or http_date(headers) or http_date(release_headers),
        }
    result["error"] = "no readable Packages index"
    result["release_only"] = True
    return result


def main():
    groups = json.loads(REPOS.read_text("utf-8"))
    urls = [s["url"] for g in groups for s in g["sources"]]
    state = json.loads(STATE.read_text("utf-8")) if STATE.exists() else {}
    status = {}

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = dict(zip(urls, pool.map(lambda u: safe_check(u, state.get(u, {})), urls)))

    for url in urls:
        prev = state.get(url, {})
        res = results[url]
        entry = {
            "versions": prev.get("versions", {}),
            "updated": prev.get("updated"),
            "latest": prev.get("latest"),
            "etag": prev.get("etag"),
            "index": prev.get("index"),
            "fails": prev.get("fails", 0),
            "failed_day": prev.get("failed_day"),
        }
        if res["ok"]:
            entry["fails"] = 0
            entry["failed_day"] = None
            entry["index"] = res.get("index")
            entry["etag"] = res.get("etag")
            if not res.get("unchanged"):
                old, new = entry["versions"], res["versions"]
                changed = [p for p, v in new.items() if old.get(p) != v]
                if old and changed:
                    entry["updated"] = now_iso()
                    entry["latest"] = [f"{p} {new[p]}" for p in changed[:3]]
                entry["versions"] = new
            entry["updated"] = entry["updated"] or res.get("seed_date")
            st = "ok"
        else:
            today = now_iso()[:10]
            if entry["failed_day"] != today:
                yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
                entry["fails"] = entry["fails"] + 1 if entry["failed_day"] == yesterday else 1
                entry["failed_day"] = today
            st = "dead" if entry["fails"] >= DEAD_AFTER else "warn"
            print(f"[{st}] {url}: {res.get('error')}", file=sys.stderr)

        state[url] = entry
        status[url] = {
            "status": st,
            "packages": len(entry["versions"]) if entry["versions"] else None,
            "updated": entry["updated"],
            "latest": entry["latest"],
        }

    for stale in set(state) - set(urls):
        del state[stale]

    STATE.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True), "utf-8")
    STATUS.write_text(json.dumps({"generated": now_iso(), "repos": status}, ensure_ascii=False, indent=1), "utf-8")
    ok = sum(1 for s in status.values() if s["status"] == "ok")
    print(f"{ok}/{len(status)} repos ok")


def safe_check(url, prev):
    try:
        return check(url, prev)
    except Exception as e:  # network errors, timeouts, malformed data
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


if __name__ == "__main__":
    main()
