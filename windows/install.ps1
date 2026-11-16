# FU#K!! G#MBLING - Windows installer. Run as Administrator.
# Usage: install.ps1 -Countries tr,za      (the GUI calls this; confirmation happens in the GUI)
#        install.ps1 -RequestUninstall      (starts 72 h cooldown)
#        install.ps1 -CancelUninstall
param([string[]]$Countries = @('global'), [switch]$RequestUninstall, [switch]$CancelUninstall)
$ErrorActionPreference = 'Stop'
$Countries = @($Countries -split ',' | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ -match '^[a-z]{2,6}$' })
$Base  = 'C:\ProgramData\FuckGambling'
$Root  = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Lists = Join-Path $Root 'lists'
$Req   = Join-Path $Base 'request\uninstall-request.txt'

if ($RequestUninstall) { Set-Content $Req (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -Encoding ASCII; 'Uninstall requested: protection ends in 72 hours.'; exit 0 }
if ($CancelUninstall)  { Remove-Item $Req -Force -ErrorAction SilentlyContinue; 'Uninstall request cancelled.'; exit 0 }

New-Item -ItemType Directory -Path $Base -Force | Out-Null
icacls $Base /grant '*S-1-5-32-544:(OI)(CI)F' | Out-Null   # allow re-install (Administrators own the folder)

function Merge($pattern, $target) {
  $all = foreach ($c in @('global') + $Countries) {
    $p = Join-Path $Lists ($pattern -f $c)
    if (Test-Path $p) { Get-Content $p -Encoding UTF8 }
  }
  Set-Content (Join-Path $Base $target) ($all | Where-Object { $_ -notmatch '^\s*#' } | Sort-Object -Unique) -Encoding ASCII
}
Merge '{0}.txt' 'block.txt'
Merge 'mirrors-{0}.txt' 'mirrors.txt'
Merge 'allow-{0}.txt' 'allow.txt'
Copy-Item (Join-Path $Lists 'help-sites.txt') (Join-Path $Base 'help-sites.txt') -Force
Copy-Item (Join-Path $PSScriptRoot 'engine.ps1') (Join-Path $Base 'engine.ps1') -Force
Set-Content (Join-Path $Base 'countries.txt') ($Countries -join ',') -Encoding ASCII
$bak = Join-Path $Base 'hosts.original'
if (-not (Test-Path $bak)) { Copy-Item "$env:SystemRoot\System32\drivers\etc\hosts" $bak -Force }

New-Item -ItemType Directory -Path (Join-Path $Base 'request') -Force | Out-Null
# SYSTEM full, Administrators/Users read-only (slows down impulsive deletion; not permanent),
# only the request folder is writable so an uninstall can be requested.
icacls $Base /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)RX' '*S-1-5-32-545:(OI)(CI)RX' | Out-Null
icacls (Join-Path $Base 'request') /grant '*S-1-5-32-544:(OI)(CI)M' | Out-Null

$action    = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Base\engine.ps1`""
$triggers  = @((New-ScheduledTaskTrigger -AtStartup), (New-ScheduledTaskTrigger -AtLogOn),
               (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 30)))
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest -LogonType ServiceAccount
Register-ScheduledTask -TaskName 'FuckGambling' -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Description 'FU#K!! G#MBLING - gambling site blocker (uninstall needs 72 h).' -Force | Out-Null

Start-ScheduledTask -TaskName 'FuckGambling'
$i = 0; do { Start-Sleep 2; $i++ } while ((Get-ScheduledTask -TaskName 'FuckGambling').State -eq 'Running' -and $i -lt 90)
Get-Content (Join-Path $Base 'log.txt') -Tail 6 -ErrorAction SilentlyContinue
'INSTALLED'
