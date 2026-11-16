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
