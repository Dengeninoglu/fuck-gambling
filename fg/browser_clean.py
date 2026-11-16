"""Remove gambling traces (history, cookies, saved logins, site data, shortcuts) from Chromium browsers.

Only rows whose site looks like gambling are touched. The browser must be closed for a real run.
"""
import os
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .blocklist import looks_like_gambling

LOCAL = Path(os.environ.get("LOCALAPPDATA", ""))
BROWSERS = {
    "Chrome": (LOCAL / "Google/Chrome/User Data", "chrome.exe"),
    "Edge": (LOCAL / "Microsoft/Edge/User Data", "msedge.exe"),
    "Brave": (LOCAL / "BraveSoftware/Brave-Browser/User Data", "brave.exe"),
    "Opera": (Path(os.environ.get("APPDATA", "")) / "Opera Software/Opera Stable", "opera.exe"),
}
SEARCH_TERM_RE = re.compile(r"(\bbet|bahis|casino|iddaa|nesine|misli|bilyoner|kupon|poker|slot|rulet|roulette|"
                            r"gambl|jackpot|hollywoodbets|betway|supabets|sportingbet|lotto|aviator|spina?\b)", re.I)


def _host(url):
    try:
        return urlsplit(url).hostname or ""
    except ValueError:
        return ""


def _is_gambling_search(url):
    try:
        q = urlsplit(url).query
    except ValueError:
        return False
    if not q:
        return False
    vals = " ".join(v for k, vs in parse_qs(q).items() if k in ("q", "p", "query", "text", "search_query", "oq") for v in vs)
    return bool(vals and SEARCH_TERM_RE.search(vals))


def profiles():
    for name, (root, exe) in BROWSERS.items():
        if not root.exists():
            continue
        if (root / "History").exists():  # Opera keeps one profile in root
            yield name, exe, root
        for p in sorted(root.iterdir()):
            if p.is_dir() and (p.name == "Default" or p.name.startswith("Profile ")) and (p / "History").exists():
                yield name, exe, p


def _open(db: Path, dry):
    if dry:  # copy so a running browser does not matter
        tmp = Path(tempfile.mkdtemp()) / db.name
        shutil.copy2(db, tmp)
        return sqlite3.connect(tmp)
    return sqlite3.connect(db)


def _sites(con, sql):
    return [r for r in con.execute(sql)]


# (file, [(select_sql returning (rowid, url_or_host), delete_sql_template, kind)])
def _clean_db(db: Path, dry, block, report, label, plan):
    if not db.exists():
        return
    try:
        con = _open(db, dry)
    except Exception as e:
        report.append(f"{label}: cannot read {db.name} ({e})")
        return
    try:
        for kind, select, delete, is_host in plan:
            try:
                rows = con.execute(select).fetchall()
            except sqlite3.Error:
                continue
            hits = [r for r in rows if r[1] and looks_like_gambling(r[1] if is_host else _host(r[1]), block)]
            if kind == "history":  # also search-result pages like google.com/search?q=betway
                hits += [r for r in rows if r[1] and r not in hits and _is_gambling_search(r[1])]
            if kind == "search terms":
                hits = [r for r in rows if r[1] and SEARCH_TERM_RE.search(r[1])]
            if hits:
                report.append((label, kind, len(hits), sorted({(r[1] if is_host or kind == 'search terms' else _host(r[1])) for r in hits})[:15]))
                if not dry:
                    con.executemany(delete, [(r[0],) for r in hits])
        if not dry:
            con.commit()
            con.execute("VACUUM")
    except sqlite3.Error as e:
        report.append(f"{label}: {db.name} not changed ({e}) - close the browser and try again")
    finally:
        con.close()


def _history_extra(con_path, dry):
    """After deleting urls, remove dangling visits / search terms / segments."""
    if dry or not con_path.exists():
        return
    con = sqlite3.connect(con_path)
    for sql in ("DELETE FROM visits WHERE url NOT IN (SELECT id FROM urls)",
                "DELETE FROM keyword_search_terms WHERE url_id NOT IN (SELECT id FROM urls)",
                "DELETE FROM segment_usage WHERE segment_id IN (SELECT id FROM segments WHERE url_id NOT IN (SELECT id FROM urls))",
                "DELETE FROM segments WHERE url_id NOT IN (SELECT id FROM urls)",
                "DELETE FROM visited_links WHERE link_url_id NOT IN (SELECT id FROM urls)"):
        try:
            con.execute(sql)
        except sqlite3.Error:
            pass
    con.commit()
    con.execute("VACUUM")
    con.close()


def clean(block, dry=True, include_logins=True):
    """Return report list. dry=True only counts."""
    report = []
    for name, exe, prof in profiles():
        label = f"{name}/{prof.name}"
        _clean_db(prof / "History", dry, block, report, label, [
            ("history", "SELECT id, url FROM urls", "DELETE FROM urls WHERE id=?", False),
            ("search terms", "SELECT url_id, term FROM keyword_search_terms", "DELETE FROM keyword_search_terms WHERE url_id=?", False),
            ("downloads", "SELECT id, tab_url FROM downloads", "DELETE FROM downloads WHERE id=?", False),
        ])
        _history_extra(prof / "History", dry)
        cookies = prof / "Network" / "Cookies"
        _clean_db(cookies if cookies.exists() else prof / "Cookies", dry, block, report, label, [
            ("cookies", "SELECT rowid, host_key FROM cookies", "DELETE FROM cookies WHERE rowid=?", True),
        ])
        if include_logins:
            for f in ("Login Data", "Login Data For Account"):
                _clean_db(prof / f, dry, block, report, label, [
                    ("saved logins", "SELECT id, origin_url FROM logins", "DELETE FROM logins WHERE id=?", False),
                ])
        _clean_db(prof / "Favicons", dry, block, report, label, [
            ("favicons", "SELECT id, page_url FROM icon_mapping", "DELETE FROM icon_mapping WHERE id=?", False),
        ])
        _clean_db(prof / "Shortcuts", dry, block, report, label, [
            ("address bar shortcuts", "SELECT id, url FROM omni_box_shortcuts", "DELETE FROM omni_box_shortcuts WHERE id=?", False),
        ])
        _clean_db(prof / "Top Sites", dry, block, report, label, [
            ("top sites", "SELECT rowid, url FROM top_sites", "DELETE FROM top_sites WHERE rowid=?", False),
        ])
        _clean_db(prof / "Network Action Predictor", dry, block, report, label, [
            ("predictions", "SELECT id, url FROM network_action_predictor", "DELETE FROM network_action_predictor WHERE id=?", False),
        ])
        # per-site storage folders (IndexedDB, File System, Service Worker caches named after origin)
        for sub in ("IndexedDB", "File System", "databases"):
            d = prof / sub
            if d.is_dir():
                hits = [p for p in d.iterdir() if looks_like_gambling(re.sub(r"^https?_|_\d+.*$", "", p.name).replace("_", "."), block)]
                if hits:
                    report.append((label, f"site data ({sub})", len(hits), [h.name for h in hits[:15]]))
                    if not dry:
                        for p in hits:
                            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    return report


def running_browsers():
    import subprocess
    out = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True).stdout.lower()
    return [n for n, (_, exe) in BROWSERS.items() if f'"{exe}"' in out]
