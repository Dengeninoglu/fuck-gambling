"""Gambling domain list: public list + country extras + mirror patterns - allowlist."""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTS = ROOT / "lists"
STEVENBLACK = "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/gambling-only/hosts"

# Host looks like gambling even if it is not on any list (used for cleaning traces, NOT for blocking).
GAMBLING_HOST_RE = re.compile(
    r"(bahis|casino|kasino|kumar|iddaa|nesine|misli\.|bilyoner|tuttur|poker|slots?\b|slot[-\d]|roulette|rulet|"
    r"gambl|sportsbook|bookmaker|1xbet|22bet|stake\.|jackpot|betting|(^|[.\-\d])bet[a-z]*\d*\.|"
    r"(^|[.\-])[a-z]*bet\d*\.|tjk\.org|bwin|unibet|pinnacle|betway|parimatch|roobet|rollbit|bc\.game)",
    re.I,
)
NOT_GAMBLING_RE = re.compile(r"(alphabet|beta|better|tibet|diabet|betterhelp|between|abet\b)", re.I)

DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9.\-]*\.[a-z]{2,}$")


def countries():
    return json.loads((LISTS / "countries.json").read_text(encoding="utf-8"))


def _read_domains(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        d = line.split("#", 1)[0].strip().lower()
        if DOMAIN_RE.match(d):
            out.append(d)
    return out


def _read_words(path):
    if not path.exists():
        return []
    return [w for w in (l.split("#", 1)[0].strip().lower() for l in path.read_text(encoding="utf-8").splitlines())
            if re.fullmatch(r"[a-z0-9\-]+", w)]


def allowlist(country):
    return set(_read_domains(LISTS / "allow-global.txt")) | set(_read_domains(LISTS / f"allow-{country}.txt"))


def is_allowed(domain, allow):
    return any(domain == a or domain.endswith("." + a) for a in allow)


def download_public(cache: Path | None = None, timeout=20):
    try:
        with urllib.request.urlopen(STEVENBLACK, timeout=timeout) as r:
            text = r.read().decode("utf-8", "replace")
        if text.count("\n0.0.0.0 ") > 1000 and cache:
            cache.write_text(text, encoding="utf-8")
    except Exception:
        text = cache.read_text(encoding="utf-8") if cache and cache.exists() else ""
    return {m.group(1).lower() for m in re.finditer(r"(?m)^0\.0\.0\.0\s+([A-Za-z0-9.\-]+)\s*$", text)} - {"0.0.0.0"}


def build(country, public=None, mirror_max=1000):
    """Return sorted list of domains to block for a country code (e.g. 'tr')."""
    block = set(public if public is not None else download_public())
    for d in _read_domains(LISTS / "global.txt") + _read_domains(LISTS / f"{country}.txt"):
        block.add(d)
        block.add("www." + d.removeprefix("www."))
    for b in _read_words(LISTS / f"mirrors-{country}.txt"):
        for tld in ("com", "net", "org", "tv", "bet", "vip", "co", "me", "live", "info", "xyz", "site", "online", "io"):
            block.update({f"{b}.{tld}", f"www.{b}.{tld}"})
        for s in ("giris", "girisi", "guncel", "guncelgiris", "yenigiris", "tv", "mobil", "bahis", "casino", "login"):
            block.add(f"{b}{s}.com")
        block.update(f"{b}{i}.com" for i in range(1, mirror_max + 1))
    allow = allowlist(country)
    return sorted(d for d in block if not is_allowed(d, allow))


def looks_like_gambling(host, blockset):
    host = host.lower().strip(".")
    if not host:
        return False
    parts = host.split(".")
    for i in range(len(parts) - 1):
        if ".".join(parts[i:]) in blockset:
            return True
    return bool(GAMBLING_HOST_RE.search(host)) and not NOT_GAMBLING_RE.search(host)
