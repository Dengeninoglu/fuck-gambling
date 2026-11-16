# FU#K!! G#MBLING

**Free, open-source gambling blocker for your PC and phone.** No account, no subscription, no tracking.
Built by someone fighting gambling addiction, for everyone who is. If it helps you, share it.

> Gambling companies spend billions to keep you playing. This costs nothing.

## What it does
| | |
|---|---|
| **1. Protect this PC** (Windows 10/11) | Blocks ~45,000 gambling domains in the hosts file, sets DNS to a filter that also blocks *new* gambling sites, stops browsers from bypassing it with their own "Secure DNS", repairs itself every 30 min. Removing it requires a **72-hour waiting period**, so an urge cannot undo it. |
| **2. Protect my phone** | **Android 9+**: sets *Private DNS* over USB (one standard, reversible setting). **iPhone**: creates a DNS profile you install with one tap. Works on Wi-Fi *and* mobile data. |
| **3. Erase gambling traces** | Removes gambling history, searches, cookies, saved logins, site data and address-bar suggestions from Chrome, Edge, Brave and Opera, and leaves everything else alone. You see what will be deleted before anything is touched. |

Banks, crypto exchanges and help/recovery sites keep working (`lists/allow-*.txt`, `lists/help-sites.txt`).

## Quick start (Windows)
1. Install [Python 3.10+](https://www.python.org/downloads/) (tick *Add to PATH*).
2. Download this repo (green **Code** button → *Download ZIP*) and unzip it.
3. Double-click **`START.bat`** → pick your country → press 1, 2, 3.

Optional for pushing the profile to an iPhone over USB: `pip install pymobiledevice3`.

## Any other device (TV, tablet, console, Mac, Linux, the whole house)
Set your **router's** DNS (or the device's DNS) to:
```
IPv4: 86.54.11.12   86.54.11.212
IPv6: 2a13:1001::86:54:11:12   2a13:1001::86:54:11:212
DNS-over-TLS (Android Private DNS): child.joindns4.eu
DNS-over-HTTPS: https://child.joindns4.eu/dns-query
```
This is [DNS4EU](https://www.joindns4.eu/) *Protective + Child Protection*, a free public resolver. It blocks gambling **and adult** content.

## Make it stick
Software alone can't stop someone who is determined, but it buys you time. That time is what you need.
- Let a **person you trust** hold the iPhone Screen Time passcode / your PC's admin password.
- On Windows, use a **standard (non-admin) account** day to day.
- Ask your bank to **block gambling transactions** on your cards.
- Use your country's **self-exclusion** scheme (GAMSTOP UK, BetStop AU, ...).
- Talk to someone. Helplines are shown in the app for your country. Worldwide: [gamblingtherapy.org](https://www.gamblingtherapy.org), [gamblersanonymous.org](https://www.gamblersanonymous.org).

## Known limits (honest)
- The DNS filter also blocks some recovery sites. On Windows the app pins them so they still open; on phones some may not open (helplines by phone always work).
- VPNs, Tor and Opera's built-in VPN bypass DNS blocking. Don't install them.
- Some hotel/work Wi-Fi networks block outside DNS. If the internet stops working there, see *Uninstall → emergency*.
- PC protection is Windows-only for now. Mac/Linux: use the router method. PRs welcome!

## Uninstall
- **Normal:** app → *Remove protection* → *Request removal*. It is removed automatically after 72 hours. You can cancel any time.
- **Phone:** Android: app → *Undo phone*, or Settings → Private DNS → Automatic. iPhone: Settings → General → VPN, DNS & Device Management → remove the profile.
- **Emergency (admin PowerShell):** see [docs/UNINSTALL.md](docs/UNINSTALL.md).

## Add your country
Edit `lists/countries.json` (name + free helplines) and optionally add `lists/<code>.txt` (gambling domains), `lists/allow-<code>.txt` (banks), `lists/mirrors-<code>.txt`. Open a pull request.

## Credits
Block lists: [StevenBlack/hosts](https://github.com/StevenBlack/hosts) (gambling-only). DNS: [DNS4EU](https://www.joindns4.eu/). License: MIT. Free forever, for any person or organisation.
