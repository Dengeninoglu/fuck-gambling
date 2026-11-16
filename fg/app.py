"""FU#K!! G#MBLING - simple GUI."""
import ctypes
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
        self.help = tk.Label(card, text="", fg="#9be39b", bg=CARD, justify="left", wraplength=540, font=("Segoe UI", 9))
        self.help.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
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
        if not messagebox.askyesno(APP_NAME, (
                "This will:\n\n"
                "• add ~10,000-45,000 gambling sites to the hosts file\n"
                "• set Wi-Fi/Ethernet DNS to DNS4EU Child Protection (blocks gambling + adult sites)\n"
                "• stop Chrome/Edge/Brave/Firefox from bypassing it with their own Secure DNS\n"
                "• re-check every 30 minutes and repair itself\n\n"
                "Banks and help sites keep working. Removing it takes a 72 hour waiting time.\n\nContinue?")):
            return
        self.run_bg(lambda: (self.log(f"Protecting this PC for: {', '.join(codes)} ..."),
                             self.ps("-Countries", ",".join(codes)) and self.log("✔ PC protected.")))

    def protect_phone(self):
        win = tk.Toplevel(self, bg=BG, padx=20, pady=16)
        win.title("Protect my phone")
        win.transient(self)
        big = ("Segoe UI", 12, "bold")
        txt = ("Segoe UI", 10)
        if self.phone.get() == "ios":
            prof = phones.ios_profile(Path.home() / "FuckGambling-DNS.mobileconfig")
            url = phones.PROFILE_URL
            tk.Label(win, text="iPhone - scan with the Camera app", fg=FG, bg=BG, font=big).pack(anchor="w")
            tk.Label(win, text="Works on any Wi-Fi or mobile data. Open the link in Safari.",
                     fg="#aaa", bg=BG, font=("Segoe UI", 9), wraplength=420, justify="left").pack(anchor="w")
            self.draw_qr(win, url).pack(pady=10)
            steps = "\n".join([
                "1. Open the iPhone Camera, point it at the code, tap the yellow link (Safari)",
                "2. 'Allow' the configuration profile download  >  Close",
                "3. Settings  >  Profile Downloaded  >  Install (top right)  >  passcode  >  Install",
                "4. Settings > General > VPN, DNS & Device Management > DNS: select FU#K!! G#MBLING",
                "5. Settings > [your name] > iCloud > Private Relay: OFF",
                "",
                "Make it stick: let someone you trust set a Screen Time passcode and turn",
                "'VPN & DNS' and 'Account Changes' to Don't Allow. (Guide: docs/IPHONE.md)",
            ])
            tk.Label(win, text=steps, fg=FG, bg=BG, font=txt, justify="left").pack(anchor="w")
            tk.Label(win, text=f"No camera? Type in iPhone Safari:  {url}", fg="#888", bg=BG,
                     font=("Consolas", 9)).pack(anchor="w", pady=(8, 0))
            self.log("iPhone profile ready. Scan the QR code with your iPhone.")
        else:
            tk.Label(win, text="Android - takes 30 seconds, no cable needed", fg=FG, bg=BG, font=big).pack(anchor="w")
            tk.Label(win, text="\n".join([
                "1. Open Settings and search for  Private DNS",
                "     (Samsung: Connections > More connection settings > Private DNS)",
                "2. Choose  'Private DNS provider hostname'",
                "3. Type exactly this and tap Save:",
            ]), fg=FG, bg=BG, font=txt, justify="left").pack(anchor="w", pady=(8, 4))
            row = tk.Frame(win, bg=BG)
            row.pack(anchor="w")
            e = tk.Entry(row, font=("Consolas", 16, "bold"), width=20, justify="center")
            e.insert(0, phones.DOT_HOST)
            e.config(state="readonly")
            e.pack(side="left")
            tk.Button(row, text="Copy", command=lambda: (self.clipboard_clear(),
                                                        self.clipboard_append(phones.DOT_HOST))).pack(side="left", padx=6)
            tk.Label(win, text="\n".join([
                "4. Test: a betting site should no longer open. Your bank still works.",
                "",
                "Make it stick: Google Family Link or Digital Wellbeing can lock settings -",
                "let someone you trust hold that password.",
            ]), fg=FG, bg=BG, font=txt, justify="left").pack(anchor="w", pady=(8, 0))
            tk.Label(win, text="Advanced: set it automatically over USB (needs USB debugging)", fg="#aaa", bg=BG,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(14, 2))
            tk.Button(win, text="Set it over USB",
                      command=lambda: self.run_bg(lambda: phones.android_protect(log=self.log))).pack(anchor="w")

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
