"""FU#K!! G#MBLING - simple GUI."""
import ctypes
import os
import re
import webbrowser
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from . import APP_NAME, __version__, blocklist, browser_clean, phones

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "windows" / "install.ps1"
NOWIN = 0x08000000
RED, BG, FG, CARD = "#e5484d", "#111214", "#f2f2f2", "#1c1d21"


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    args = "" if getattr(sys, "frozen", False) else " ".join(f'"{a}"' for a in ["-m", "fg"] + sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, args, str(ROOT), 1)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  v{__version__}")
        self.configure(bg=BG)
        self.geometry("620x640")
        self.minsize(520, 560)
        self.countries = blocklist.countries()
        codes = [c for c in self.countries if not c.startswith("_")]
        self.names = {self.countries[c]["name"]: c for c in codes}

        tk.Label(self, text=APP_NAME, fg=RED, bg=BG, font=("Segoe UI Black", 26)).pack(pady=(18, 0))
        tk.Label(self, text="Free. Open source. Blocks gambling on your PC and phone.", fg=FG, bg=BG,
                 font=("Segoe UI", 10)).pack()

        card = tk.Frame(self, bg=CARD, padx=16, pady=12)
        card.pack(fill="x", padx=16, pady=12)
        tk.Label(card, text="Your country", fg=FG, bg=CARD, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.country = ttk.Combobox(card, values=list(self.names), state="readonly", width=24)
        self.country.set(self.countries["global"]["name"])
        self.country.grid(row=0, column=1, sticky="w", padx=8)
        tk.Label(card, text="Also block (optional)", fg=FG, bg=CARD, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.country2 = ttk.Combobox(card, values=["-"] + list(self.names), state="readonly", width=24)
        self.country2.set("-")
        self.country2.grid(row=1, column=1, sticky="w", padx=8, pady=(6, 0))
        tk.Label(card, text="Your phone", fg=FG, bg=CARD, font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.phone = tk.StringVar(value="android")
        pf = tk.Frame(card, bg=CARD)
        pf.grid(row=2, column=1, sticky="w", padx=8, pady=(6, 0))
        for val, txt in (("android", "Android"), ("ios", "iPhone")):
            tk.Radiobutton(pf, text=txt, variable=self.phone, value=val, fg=FG, bg=CARD, selectcolor=BG,
                           activebackground=CARD, activeforeground=FG).pack(side="left", padx=(0, 12))
        self.strict = tk.BooleanVar(value=False)
        tk.Checkbutton(card, text="Strict PC mode: also block adult sites (DNS filter, catches new gambling sites faster)",
                       variable=self.strict, fg="#aaa", bg=CARD, selectcolor=BG, activebackground=CARD,
                       activeforeground=FG, font=("Segoe UI", 9), wraplength=520, justify="left").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.help = tk.Label(card, text="", fg="#9be39b", bg=CARD, justify="left", wraplength=540, font=("Segoe UI", 9))
        self.help.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.country.bind("<<ComboboxSelected>>", lambda e: self.show_help())
        self.show_help()

        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=16)
        self.buttons = []
        for txt, fn in (("1  Protect this PC", self.protect_pc),
                        ("2  Protect my phone", self.protect_phone),
                        ("3  Erase gambling traces from browsers", self.clean_browsers)):
            b = tk.Button(btns, text=txt, command=fn, bg=RED, fg="white", activebackground="#c13b40", relief="flat",
                          font=("Segoe UI", 11, "bold"), pady=8, cursor="hand2")
            b.pack(fill="x", pady=4)
            self.buttons.append(b)
        tk.Button(btns, text="Remove protection (72 h waiting time)...", command=self.undo, bg=BG, fg="#888",
                  relief="flat", activebackground=BG, cursor="hand2").pack(pady=(2, 0))

        self.log_box = tk.Text(self, height=10, bg=CARD, fg=FG, relief="flat", font=("Consolas", 9), wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        self.log("Ready. Pick your country, then press 1, 2 and 3.")
        if not is_admin():
            self.log("Note: not running as Administrator - button 1 will ask for permission.")

    # ---------- helpers ----------
    def codes(self):
        c = [self.names[self.country.get()]]
        if self.country2.get() in self.names:
            c.append(self.names[self.country2.get()])
        return [x for x in dict.fromkeys(c)]

    def show_help(self):
        c = self.names[self.country.get()]
        lines = self.countries[c]["help"] + ([] if c == "global" else self.countries["global"]["help"][:1])
        self.help.config(text="Need to talk to someone now?\n" + "\n".join("•  " + h for h in lines))

    def log(self, msg):
        def add():
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
        self.after(0, add)

    def run_bg(self, fn):
        def wrap():
            for b in self.buttons:
                b.config(state="disabled")
            try:
                fn()
            except Exception as e:
                self.log(f"ERROR: {e}")
            finally:
                for b in self.buttons:
                    self.after(0, lambda b=b: b.config(state="normal"))
        threading.Thread(target=wrap, daemon=True).start()

    def ps(self, *args):
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(INSTALL), *args],
                           capture_output=True, text=True, creationflags=NOWIN)
        for line in (r.stdout + r.stderr).splitlines():
            if line.strip():
                self.log(line)
        return r.returncode == 0

    # ---------- actions ----------
    def protect_pc(self):
        if not is_admin():
            if messagebox.askyesno(APP_NAME, "Protecting the PC needs Administrator rights.\nRestart the app as Administrator?"):
                relaunch_as_admin()
                self.destroy()
            return
        codes = self.codes()
        strict = self.strict.get()
        dns_line = ("• set Wi-Fi/Ethernet DNS to DNS4EU Child Protection - this ALSO blocks adult sites\n" if strict
                    else "• block gambling only - nothing else is blocked\n")
        if not messagebox.askyesno(APP_NAME, (
                "This will:\n\n"
                "• add ~45,000 gambling sites to the hosts file\n" + dns_line +
                "• stop Chrome/Edge/Brave/Firefox from skipping it with their own Secure DNS\n"
                "• re-check every 30 minutes and repair itself\n\n"
                "Banks and help sites keep working. Removing it takes a 72 hour waiting time.\n\nContinue?")):
            return
        args = ["-Countries", ",".join(codes)] + (["-Strict"] if strict else [])
        self.run_bg(lambda: (self.log(f"Protecting this PC for: {', '.join(codes)}" + (" (strict)" if strict else "") + " ..."),
                             self.ps(*args) and self.log("✔ PC protected.")))

    # ---------- phone ----------
    def _id_file(self):
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FuckGambling" / "nextdns-id.txt"

    def _saved_id(self):
        try:
            v = self._id_file().read_text(encoding="utf-8").strip().lower()
            return v if re.fullmatch(r"[0-9a-f]{6}", v) else ""
        except OSError:
            return ""

    def protect_phone(self):
        win = tk.Toplevel(self, bg=BG, padx=20, pady=16)
        win.title("Protect my phone")
        win.transient(self)
        ios = self.phone.get() == "ios"
        name = "iPhone" if ios else "Android"
        mode = tk.StringVar(value="A")
        tk.Label(win, text=f"Protect your {name} - choose one:", fg=FG, bg=BG,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        row = tk.Frame(win, bg=BG)
        row.pack(fill="x", pady=(8, 4))
        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True)

        def option(val, title, sub):
            return tk.Radiobutton(row, text=f"{title}\n{sub}", variable=mode, value=val, indicatoron=0,
                                  command=lambda: render(), bg=CARD, fg=FG, selectcolor=RED, activebackground=CARD,
                                  activeforeground=FG, relief="flat", bd=0, padx=10, pady=8, width=26,
                                  font=("Segoe UI", 10, "bold"), cursor="hand2")
        option("A", "A  Gambling only", "free NextDNS account · 3 min").pack(side="left", padx=(0, 6), fill="x", expand=True)
        option("B", "B  No account · 1 min", "also blocks adult sites").pack(side="left", fill="x", expand=True)

        def label(text, color=FG, size=10, bold=False, pady=0):
            tk.Label(body, text=text, fg=color, bg=BG, justify="left", wraplength=520,
                     font=("Segoe UI", size, "bold" if bold else "normal")).pack(anchor="w", pady=pady)

        def show_qr(url, steps):
            label(f"Scan with the {name} camera" + (" and open the link in Safari" if ios else " (or Google Lens)"), bold=True, pady=(10, 0))
            self.draw_qr(body, url, box=5).pack(pady=8)
            label("\n".join(steps))
            tk.Label(body, text=f"No camera? Open on the phone:  {url}", fg="#888", bg=BG, font=("Consolas", 8),
                     wraplength=540, justify="left").pack(anchor="w", pady=(8, 0))

        def render():
            for c in body.winfo_children():
                c.destroy()
            if mode.get() == "B":
                label("Uses the free public DNS4EU filter. Blocks gambling AND adult sites. No account needed.", "#f0c96b", 9)
                if ios:
                    show_qr(phones.PROFILE_URL, [
                        "1. Tap Allow  >  Close",
                        "2. Settings  >  Profile Downloaded  >  Install  >  passcode  >  Install",
                        "3. Settings > General > VPN, DNS & Device Management > DNS > FU#K!! G#MBLING",
                    ])
                else:
                    show_qr(phones.ANDROID_URL + "#b", [
                        "1. Tap Copy on the page",
                        "2. Settings > Private DNS > Private DNS provider hostname > Paste > Save",
                    ])
                    tk.Button(body, text="Or set it automatically over USB (needs USB debugging)",
                              command=lambda: self.run_bg(lambda: phones.android_protect(log=self.log))).pack(anchor="w", pady=(10, 0))
                return
            nid = self._saved_id()
            if nid:
                label(f"Your NextDNS ID: {nid}   (only gambling is blocked)", "#8be09b", 9)
                show_qr(f"{phones.GAMBLING_ONLY_URL}?id={nid}&p={'iphone' if ios else 'android'}",
                        ["1. Tap Install profile  >  Allow  >  Close",
                         "2. Settings  >  Profile Downloaded  >  Install",
                         "3. Settings > General > VPN, DNS & Device Management > DNS > FU#K!! G#MBLING"] if ios else
                        ["1. Tap Copy on the page",
                         "2. Settings > Private DNS > Private DNS provider hostname > Paste > Save"])
                tk.Button(body, text="Use a different NextDNS ID", command=lambda: (self._id_file().unlink(missing_ok=True), render())).pack(anchor="w", pady=(10, 0))
                return
            label("Do this part here on the computer (3 minutes), then scan one QR code with the phone.", "#aaa", 9, pady=(4, 6))
            label("Step 1", bold=True)
            tk.Button(body, text="Open NextDNS sign-up (free)", bg=RED, fg="white", relief="flat", font=("Segoe UI", 10, "bold"),
                      cursor="hand2", command=lambda: webbrowser.open("https://my.nextdns.io/signup")).pack(anchor="w", pady=(2, 8))
            label("Step 2", bold=True)
            label("In NextDNS: Parental Control tab  >  Categories  >  Add a category  >  Gambling", pady=(0, 8))
            label("Step 3", bold=True)
            label("Setup tab  >  copy your ID (6 characters) and paste it here:")
            r = tk.Frame(body, bg=BG)
            r.pack(anchor="w", pady=4)
            e = tk.Entry(r, font=("Consolas", 16, "bold"), width=10, justify="center")
            e.pack(side="left")
            err = tk.Label(body, text="", fg=RED, bg=BG, font=("Segoe UI", 9))

            def save():
                v = e.get().strip().lower()
                m = re.search(r"[0-9a-f]{6}", v)
                if not m:
                    err.config(text="That doesn't look like a NextDNS ID (6 characters like abc123).")
                    err.pack(anchor="w")
                    return
                f = self._id_file()
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(m.group(0), encoding="utf-8")
                self.log(f"NextDNS ID saved: {m.group(0)}")
                render()
            tk.Button(r, text="Show my QR code", command=save, bg=RED, fg="white", relief="flat",
                      font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left", padx=8)
            e.bind("<Return>", lambda ev: save())
            e.focus_set()

        render()

    def draw_qr(self, parent, data, box=6):
        import qrcode
        qr = qrcode.QRCode(border=2, box_size=1)
        qr.add_data(data)
        qr.make(fit=True)
        m = qr.get_matrix()
        c = tk.Canvas(parent, width=len(m) * box, height=len(m) * box, bg="white", highlightthickness=0)
        for y, row in enumerate(m):
            for x, v in enumerate(row):
                if v:
                    c.create_rectangle(x * box, y * box, (x + 1) * box, (y + 1) * box, fill="black", outline="black")
        return c

    def clean_browsers(self):
        def work():
            self.log("Scanning browsers (nothing deleted yet)...")
            public = blocklist.download_public()
            block = set()
            for c in ["global"] + self.codes():
                block |= set(blocklist.build(c, public))
            rep = browser_clean.clean(block, dry=True)
            totals = {}
            for r in rep:
                if isinstance(r, tuple):
                    totals[r[1]] = totals.get(r[1], 0) + r[2]
            if not totals:
                self.log("No gambling traces found. ✔")
                return
            summary = "\n".join(f"• {k}: {v}" for k, v in totals.items())
            self.log("Found:\n" + summary)
            ok = []
            self.after(0, lambda: ok.append(messagebox.askyesno(APP_NAME, (
                f"Found gambling traces:\n\n{summary}\n\nDelete them permanently?\n"
                "Open browsers will be closed (tabs come back when you reopen)."))))
            while not ok:
                time.sleep(0.2)
            if not ok[0]:
                self.log("Cancelled.")
                return
            for name in browser_clean.running_browsers():
                exe = browser_clean.BROWSERS[name][1]
                subprocess.run(["taskkill", "/im", exe], capture_output=True, creationflags=NOWIN)
                time.sleep(3)
                subprocess.run(["taskkill", "/f", "/im", exe], capture_output=True, creationflags=NOWIN)
            time.sleep(2)
            rep = browser_clean.clean(block, dry=False)
            errors = [r for r in rep if isinstance(r, str)]
            for e in errors:
                self.log("! " + e)
            self.log("✔ Gambling traces erased." if not errors else "Done with some errors (see above).")
            self.log("If browser sync is on, also delete synced history at myactivity.google.com "
                     "and saved passwords at passwords.google.com.")
        self.run_bg(work)

    def undo(self):
        win = tk.Toplevel(self, bg=BG, padx=16, pady=16)
        win.title("Remove protection")
        tk.Label(win, fg=FG, bg=BG, justify="left", wraplength=420, text=(
            "Removing PC protection takes 72 hours. The urge will pass long before that.\n"
            "If you want to gamble right now, call the helpline first:\n\n" + self.help.cget("text"))).pack()
        r = tk.Frame(win, bg=BG)
        r.pack(pady=10)
        def req():
            if is_admin():
                self.run_bg(lambda: self.ps("-RequestUninstall"))
            else:
                messagebox.showinfo(APP_NAME, "Run the app as Administrator to request removal.")
            win.destroy()
        tk.Button(r, text="Request removal (72 h)", command=req).pack(side="left", padx=4)
        tk.Button(r, text="Cancel a request", command=lambda: (self.run_bg(lambda: self.ps("-CancelUninstall")), win.destroy())).pack(side="left", padx=4)
        tk.Button(r, text="Undo phone (Android)", command=lambda: (self.run_bg(lambda: phones.android_protect(log=self.log, undo=True)), win.destroy())).pack(side="left", padx=4)


def main():
    if sys.platform != "win32":
        print("The PC part currently supports Windows. Phone + router guides: see README.")
    App().mainloop()
