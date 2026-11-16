<p align="center"><img src="docs/img/icon.png" width="96" alt=""></p>

<h1 align="center">FU#K!! G#MBLING</h1>

<p align="center"><b>Block every betting and casino site on your computer and your phone.<br>
Free forever. Non-profit. No account. No ads. No data collected.</b></p>

<p align="center">
  <a href="https://github.com/Dengeninoglu/fuck-gambling/releases/latest/download/FuckGambling.exe"><img alt="Download for Windows" src="https://img.shields.io/badge/DOWNLOAD-Windows%2010%20%2F%2011-e5484d?style=for-the-badge&logo=windows&logoColor=white"></a>
</p>

<p align="center"><i>Made for everyone who wants out.</i></p>

---

## 🤝 A non-profit project
FU#K!! G#MBLING is a **non-profit, volunteer project**. We don't sell anything, show ads or collect data, and we don't take a cut.
Gambling companies spend billions to keep people playing. This costs nothing and always will.

**Organisations** fighting gambling harm (helplines, clinics, charities, regulators): you may use, translate, rebrand and hand this out for free (MIT license). Open an issue and we'll help you set it up for your country.

---

## How to use it (3 minutes)

### Step 1 · Download and open
1. Click the red **DOWNLOAD** button above.
2. Open **FuckGambling.exe**. Windows asks *"Do you want to allow this app to make changes?"*, click **Yes**.
   > If a blue box says *"Windows protected your PC"*, click **More info → Run anyway**. Small free apps without a paid certificate always show this. The full source code is on this page.
3. Choose **your country** (this shows your local helpline) and **your phone** (Android or iPhone).

<p align="center"><img src="docs/img/main.png" width="460" alt="Main window"></p>

### Step 2 · Press the three buttons

| Button | What happens |
|---|---|
| **1 Protect this PC** | Blocks ~45,000 betting/casino sites, plus new ones as they appear. Works in **every browser**. Repairs itself every 30 minutes. |
| **2 Protect my phone** | **iPhone:** scan the QR code with the Camera app, then tap *Install*. **Android:** type one word into *Settings → Private DNS*. No cable needed. |
| **3 Erase gambling traces** | Deletes gambling history, searches, cookies, saved logins and suggestions from Chrome, Edge, Brave and Opera. Everything else stays. You see a list first. |

<p align="center">
<img src="docs/img/iphone.png" width="380" alt="iPhone setup">&nbsp;&nbsp;
<img src="docs/img/android.png" width="380" alt="Android setup">
</p>

> 📱 **No computer? Set up your phone directly:**
> **iPhone:** open [this link in Safari](https://dengeninoglu.github.io/fuck-gambling/FuckGambling.mobileconfig) → *Allow* → Settings → *Profile Downloaded* → *Install* → then Settings → General → VPN, DNS & Device Management → DNS → select *FU#K!! G#MBLING*.
> **Android 9+:** Settings → search *Private DNS* → *Private DNS provider hostname* → type `child.joindns4.eu` → Save.

### Step 3 · Make it stick (most important)
A blocker buys you time. These steps make sure an urge can't undo it in a weak moment:
- 🔑 **Give a code to someone you trust.** iPhone: let them set the *Screen Time* passcode. Android: *Google Family Link*. They keep it, not you.
- 🏦 **Ask your bank to block gambling payments** on your cards (most banking apps have this).
- 🚫 **Self-exclude** from betting companies if your country has a scheme (GAMSTOP UK, BetStop Australia, …).
- 📞 **Talk to someone.** The app shows free helplines for your country.

---

## ✅ What keeps working
Banking apps, crypto exchanges, work, school, YouTube, social media and **help & recovery sites**. Only gambling is blocked.

## ❓ FAQ
**Can I turn it off?** Yes, on purpose slowly: *Remove protection* starts a **72-hour waiting time**. The urge passes long before that. You can cancel the request any time.
**Does it break my phone?** No. It only changes the phone's standard *Private DNS* / DNS profile setting, and you can switch it back in Settings.
**Does it track me?** No. There is no server, no account and no analytics. It runs on your device only.
**Mac / TV / tablet / the whole house?** Set your router's DNS to `86.54.11.12` and `86.54.11.212` (instructions are usually under *Internet / DNS* in the router page).
**I already use Gamban / BetBlocker.** Fine. The app detects them and adds its block list on top without fighting them.

## Need help right now?
| Country | Free helpline |
|---|---|
| 🇿🇦 South Africa | **0800 006 008** (SA Responsible Gambling Foundation, 24/7) |
| 🇬🇧 United Kingdom | **0808 8020 133** (National Gambling Helpline, 24/7) |
| 🇺🇸 United States | **1-800-GAMBLER** |
| 🇦🇺 Australia | **1800 858 858** (Gambling Help, 24/7) |
| 🇹🇷 Türkiye | **115** (YEDAM, 7/24) |
| 🌍 Anywhere | [gamblingtherapy.org](https://www.gamblingtherapy.org) (free, online, many languages) · [Gamblers Anonymous](https://www.gamblersanonymous.org) |

---

<details>
<summary><b>For techies: how it works, building, contributing</b></summary>

- **PC (Windows 10/11):** `windows/engine.ps1` runs as a SYSTEM scheduled task (startup, logon, every 30 min). It writes [StevenBlack gambling-only](https://github.com/StevenBlack/hosts) hosts + country lists + numbered-mirror patterns into the hosts file, pins help sites to real IPs, sets adapter DNS to [DNS4EU](https://www.joindns4.eu/) *Protective + Child Protection* (with DoH), and locks Chrome/Edge/Brave/Firefox DoH via policy. Uninstall uses a 72 h cooldown file. Emergency removal: [docs/UNINSTALL.md](docs/UNINSTALL.md).
- **Android:** Private DNS `child.joindns4.eu` (DoT). Optional USB/adb automation.
- **iPhone:** `com.apple.dnsSettings.managed` profile served over local Wi-Fi via QR. Guide: [docs/IPHONE.md](docs/IPHONE.md).
- **Run from source:** Python 3.10+, `pip install qrcode`, then `START.bat` (or `python -m fg`).
- **Build exe:** `pip install pyinstaller qrcode` then PyInstaller `--onefile --windowed --uac-admin` with `lists` and `windows` as data (see release notes).
- **Add your country:** edit `lists/countries.json` (name + free helplines) and add `lists/<code>.txt` (gambling sites), `lists/allow-<code>.txt` (banks), `lists/mirrors-<code>.txt`. PRs welcome!

**Known limits:** VPNs/Tor bypass DNS blocking. On phones the DNS filter also hides some recovery websites (phone helplines always work). A determined admin can remove anything on their own PC. That is why Step 3 matters.

</details>

<p align="center"><sub>MIT License · Block lists: StevenBlack/hosts · DNS: DNS4EU · Made with anger and hope.</sub></p>
