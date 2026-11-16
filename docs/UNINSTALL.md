# Emergency uninstall (Windows)

Give this file to the person you trust, not to yourself. The normal way is the 72-hour request in the app.

Open **PowerShell as Administrator** and run:

```powershell
Unregister-ScheduledTask -TaskName FuckGambling -Confirm:$false
Get-NetAdapter -Physical | ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ResetServerAddresses }
'Google\Chrome','Microsoft\Edge','BraveSoftware\Brave' | ForEach-Object { Remove-ItemProperty "HKLM:\SOFTWARE\Policies\$_" -Name DnsOverHttpsMode -ErrorAction SilentlyContinue }
Remove-Item HKLM:\SOFTWARE\Policies\Mozilla\Firefox\DNSOverHTTPS -Recurse -ErrorAction SilentlyContinue
takeown /f C:\ProgramData\FuckGambling /r /d y; icacls C:\ProgramData\FuckGambling /reset /t
Copy-Item C:\ProgramData\FuckGambling\hosts.original C:\Windows\System32\drivers\etc\hosts -Force
Remove-Item C:\ProgramData\FuckGambling -Recurse -Force
ipconfig /flushdns
```
(On non-English Windows the `/d y` answer letter may differ, e.g. `/d E` in Turkish.)

Pause only, without removing: `Disable-ScheduledTask -TaskName FuckGambling` (resume: `Enable-ScheduledTask`).
