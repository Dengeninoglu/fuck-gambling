"""Phone protection. Only standard, reversible OS settings are used - nothing that can brick a phone.

Android: sets Private DNS (Settings > Network > Private DNS) over USB debugging with adb.
iPhone : builds a DNS configuration profile; pushes it over USB (user taps Install on the phone)
         or the user opens the file from Mail / Files.
"""
import http.server
import io
import os
import socket
import threading
import shutil
import subprocess
import sys
import uuid
import zipfile
import urllib.request
from pathlib import Path

DOT_HOST = "child.joindns4.eu"          # DNS-over-TLS hostname for Android Private DNS
DOH_URL = "https://child.joindns4.eu/dns-query"
# Same profile, hosted publicly so the QR code works on any network (mobile data too).
PROFILE_URL = "https://dengeninoglu.github.io/fuck-gambling/FuckGambling.mobileconfig"
ANDROID_URL = "https://dengeninoglu.github.io/fuck-gambling/android/"
IPHONE_URL = "https://dengeninoglu.github.io/fuck-gambling/iphone/"
GAMBLING_ONLY_URL = "https://dengeninoglu.github.io/fuck-gambling/a/"
DNS_IPS = ["86.54.11.12", "86.54.11.212", "2a13:1001::86:54:11:12", "2a13:1001::86:54:11:212"]
PLATFORM_TOOLS = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
TOOLS = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FuckGambling" / "tools"
FROZEN = getattr(sys, "frozen", False)
NOWIN = 0x08000000 if sys.platform == "win32" else 0


# ---------------- Android ----------------
def adb_path(download=True, log=print):
    found = shutil.which("adb") or (TOOLS / "platform-tools" / "adb.exe")
    if Path(found).exists():
        return str(found)
    if not download:
        return None
    log("Downloading Android platform-tools from Google (~7 MB)...")
    data = urllib.request.urlopen(PLATFORM_TOOLS, timeout=60).read()
    TOOLS.mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(data)).extractall(TOOLS)
    return str(TOOLS / "platform-tools" / "adb.exe")


def _adb(adb, *args, timeout=20):
    r = subprocess.run([adb, *args], capture_output=True, text=True, timeout=timeout, creationflags=NOWIN)
    return (r.stdout + r.stderr).strip()


def android_devices(adb):
    out = _adb(adb, "devices")
    devs = [l.split("\t") for l in out.splitlines()[1:] if "\t" in l]
    return [(serial, state) for serial, state in devs]


def android_protect(log=print, undo=False):
    adb = adb_path(log=log)
    devs = android_devices(adb)
    if not devs:
        raise RuntimeError("No Android phone found. Plug in the USB cable and turn on USB debugging "
                           "(Settings > About phone > tap 'Build number' 7 times > Developer options > USB debugging).")
    serial, state = devs[0]
    if state == "unauthorized":
        raise RuntimeError("On the phone, tap 'Allow' on the 'Allow USB debugging?' popup, then try again.")
    if state != "device":
        raise RuntimeError(f"Phone state is '{state}'. Reconnect the cable and try again.")
    sdk = _adb(adb, "-s", serial, "shell", "getprop", "ro.build.version.sdk")
    if not sdk.isdigit() or int(sdk) < 28:
        raise RuntimeError("This phone is older than Android 9 and has no Private DNS. Use the router method (README).")
    model = _adb(adb, "-s", serial, "shell", "getprop", "ro.product.model")
    if undo:
        _adb(adb, "-s", serial, "shell", "settings", "put", "global", "private_dns_mode", "opportunistic")
        _adb(adb, "-s", serial, "shell", "settings", "delete", "global", "private_dns_specifier")
        log(f"{model}: Private DNS set back to Automatic.")
        return
    _adb(adb, "-s", serial, "shell", "settings", "put", "global", "private_dns_specifier", DOT_HOST)
    _adb(adb, "-s", serial, "shell", "settings", "put", "global", "private_dns_mode", "hostname")
    mode = _adb(adb, "-s", serial, "shell", "settings", "get", "global", "private_dns_mode")
    spec = _adb(adb, "-s", serial, "shell", "settings", "get", "global", "private_dns_specifier")
    if mode != "hostname" or spec != DOT_HOST:
        raise RuntimeError(f"Phone did not accept the setting (mode={mode}, host={spec}).")
    log(f"{model}: Private DNS = {DOT_HOST}. Gambling sites are now blocked on Wi-Fi and mobile data.")
    log("Now turn OFF USB debugging on the phone (Developer options) - it is not needed any more.")


# ---------------- iPhone ----------------
def ios_profile(path: Path):
    ips = "".join(f"<string>{ip}</string>" for ip in DNS_IPS)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>PayloadContent</key><array><dict>
<key>DNSSettings</key><dict><key>DNSProtocol</key><string>HTTPS</string><key>ServerURL</key><string>{DOH_URL}</string>
<key>ServerAddresses</key><array>{ips}</array></dict>
<key>PayloadDisplayName</key><string>FU#K!! G#MBLING DNS</string>
<key>PayloadIdentifier</key><string>org.fuckgambling.dns.payload</string>
<key>PayloadType</key><string>com.apple.dnsSettings.managed</string>
<key>PayloadUUID</key><string>{str(uuid.uuid4()).upper()}</string><key>PayloadVersion</key><integer>1</integer>
</dict></array>
<key>PayloadDescription</key><string>Blocks gambling sites on Wi-Fi and mobile data (DNS4EU Child Protection, encrypted).</string>
<key>PayloadDisplayName</key><string>FU#K!! G#MBLING</string>
<key>PayloadIdentifier</key><string>org.fuckgambling.dns</string>
<key>PayloadType</key><string>Configuration</string>
<key>PayloadUUID</key><string>{str(uuid.uuid4()).upper()}</string><key>PayloadVersion</key><integer>1</integer>
</dict></plist>"""
    path.write_text(xml, encoding="utf-8")
    return path


def ios_protect(out_dir: Path, log=print):
    prof = ios_profile(out_dir / "FuckGambling-DNS.mobileconfig")
    log(f"Profile saved: {prof}")
    if FROZEN:
        return prof
    try:  # optional: push over USB with pymobiledevice3 (pip install pymobiledevice3)
        r = subprocess.run([sys.executable, "-m", "pymobiledevice3", "profile", "install", str(prof)],
                           capture_output=True, text=True, timeout=60, creationflags=NOWIN)
        if r.returncode == 0:
            log("Sent to iPhone. On the phone: Settings > 'Profile Downloaded' > Install.")
            return prof
        log("Could not push over USB (" + (r.stderr.strip().splitlines() or ["no device"])[-1][:120] + ").")
    except Exception as e:
        log(f"USB push not available ({e.__class__.__name__}).")
    log("Email the profile to yourself and open it in the iPhone Mail app, then Settings > 'Profile Downloaded' > Install.")
    return prof


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


_server = None


def serve_profile(prof: Path, port=8765):
    """Serve the profile on the local Wi-Fi so an iPhone can open it from a QR code. Returns URL."""
    global _server
    data = prof.read_bytes()

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/fg.mobileconfig"):
                self.send_response(200)
                self.send_header("Content-Type", "application/x-apple-aspen-config")
                self.send_header("Content-Disposition", 'attachment; filename="FuckGambling.mobileconfig"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(302)
                self.send_header("Location", "/fg.mobileconfig")
                self.end_headers()

        def log_message(self, *a):
            pass

    if _server is None:
        for p in range(port, port + 20):
            try:
                _server = http.server.ThreadingHTTPServer(("0.0.0.0", p), H)
                break
            except OSError:
                continue
        threading.Thread(target=_server.serve_forever, daemon=True).start()
    else:
        _server.RequestHandlerClass = H
    return f"http://{lan_ip()}:{_server.server_address[1]}/fg.mobileconfig"


# ---------------- NextDNS check ----------------
def _dns_query(name):
    import struct
    head = struct.pack(">HHHHHH", 0, 0x0100, 1, 0, 0, 0)
    body = b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\x00" + struct.pack(">HH", 1, 1)
    return head + body


def _dns_answers(resp):
    import struct
    count = struct.unpack(">H", resp[6:8])[0]
    i = 12
    while resp[i]:
        i += resp[i] + 1
    i += 5
    ips = []
    for _ in range(count):
        if resp[i] & 0xC0 == 0xC0:
            i += 2
        else:
            while resp[i]:
                i += resp[i] + 1
            i += 1
        rtype, _, _, ln = struct.unpack(">HHIH", resp[i:i + 10])
        i += 10
        if rtype == 1:
            ips.append(".".join(map(str, resp[i:i + 4])))
        i += ln
    return resp[3] & 15, ips


def nextdns_blocks_gambling(profile_id, timeout=8):
    """True if this NextDNS profile blocks well-known betting sites, False if not, None if it can't be checked."""
    results = []
    for name in ("bet365.com", "betway.com", "1xbet.com"):
        try:
            req = urllib.request.Request(f"https://dns.nextdns.io/{profile_id}", data=_dns_query(name),
                                         headers={"content-type": "application/dns-message",
                                                  "accept": "application/dns-message"})
            rcode, ips = _dns_answers(urllib.request.urlopen(req, timeout=timeout).read())
            results.append(rcode == 3 or not ips or all(ip == "0.0.0.0" for ip in ips))
        except Exception:
            continue
    if not results:
        return None
    return sum(results) >= 2 if len(results) >= 2 else results[0]


# ---------------- NextDNS automatic setup (option A) ----------------
NEXTDNS_API = "https://api.nextdns.io"
NEXTDNS_PROFILE_NAME = "FU#K!! G#MBLING"


def _api(api_key, method, path, body=None, timeout=15):
    import json
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(NEXTDNS_API + path, data=data, method=method,
                                 headers={"X-Api-Key": api_key, "Content-Type": "application/json",
                                          "User-Agent": "fuck-gambling"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {}


def nextdns_setup(api_key, log=print):
    """Use the user's NextDNS API key to make a profile that blocks gambling (+ bypass methods).
    Returns the profile ID. The key is only used for these calls and is never stored."""
    import time
    api_key = api_key.strip()
    status, res = _api(api_key, "GET", "/profiles")
    if status in (401, 403):
        raise RuntimeError("NextDNS did not accept this API key. Copy it again from my.nextdns.io/account.")
    if status != 200:
        raise RuntimeError(f"Could not reach NextDNS (error {status}). Check the internet connection.")
    profiles = res.get("data", [])
    ours = [p for p in profiles if p.get("name") == NEXTDNS_PROFILE_NAME]
    if ours:
        pid = ours[0]["id"]
    elif profiles:
        pid = profiles[0]["id"]  # a new account comes with one empty profile - use it
    else:
        status, res = _api(api_key, "POST", "/profiles", {"name": NEXTDNS_PROFILE_NAME})
        if status not in (200, 201):
            raise RuntimeError(f"Could not create a NextDNS profile (error {status}).")
        pid = res["data"]["id"]
    log(f"NextDNS profile: {pid}")
    # gambling category on (add it, or switch it on if it already exists)
    status, _ = _api(api_key, "PATCH", f"/profiles/{pid}/parentalControl/categories/gambling", {"active": True})
    if status == 404:
        status, _ = _api(api_key, "POST", f"/profiles/{pid}/parentalControl/categories", {"id": "gambling", "active": True})
    if status not in (200, 201, 204):
        raise RuntimeError(f"Could not turn on the Gambling category (error {status}).")
    log("Gambling category: ON")
    status, _ = _api(api_key, "PATCH", f"/profiles/{pid}/parentalControl", {"blockBypass": True})
    log("Block Bypass Methods (VPN/proxy/Tor): " + ("ON" if status in (200, 204) else f"could not set (error {status})"))
    # help & recovery sites must never be blocked (the gambling category hides some of them)
    try:
        from .blocklist import LISTS
        helps = [l.split("#", 1)[0].strip().lower() for l in (LISTS / "help-sites.txt").read_text(encoding="utf-8").splitlines()]
        helps = [h for h in helps if h]
    except OSError:
        helps = []
    added = 0
    for h in helps:
        st, _ = _api(api_key, "POST", f"/profiles/{pid}/allowlist", {"id": h, "active": True})
        added += st in (200, 201, 204, 409)
    if helps:
        log(f"Help & recovery sites kept open: {added}/{len(helps)}")
    for _ in range(12):  # NextDNS needs a few seconds to apply
        if nextdns_blocks_gambling(pid):
            log("Test: betting sites are blocked ✔")
            return pid
        time.sleep(5)
    log("Settings saved, but the test does not show blocking yet. Try 'Check again' in a minute.")
    return pid
