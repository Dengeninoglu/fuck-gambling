# FU#K!! G#MBLING - Windows engine
# Runs as SYSTEM from the scheduled task "FuckGambling" (at startup, logon, every 30 min).
# - writes the gambling block list into the hosts file (between markers, other lines untouched)
# - pins help/recovery sites to their real IPs (the DNS filter blocks some of them)
# - sets Wi-Fi/Ethernet DNS to DNS4EU Child Protection (+ DoH), browsers cannot use their own DoH
# - re-applies everything if someone changes it; uninstall only after a 72 h cooldown request
$ErrorActionPreference = 'Continue'
$Base      = 'C:\ProgramData\FuckGambling'
$HostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
$LogPath   = Join-Path $Base 'log.txt'
$Cache     = Join-Path $Base 'public-list.txt'
$Request   = Join-Path $Base 'request\uninstall-request.txt'
$MarkStart = '# >>> FUCK-GAMBLING START (managed, rewritten every 30 min)'
$MarkEnd   = '# <<< FUCK-GAMBLING END'
$CooldownHours = 72
$Dns4   = @('86.54.11.12', '86.54.11.212')
$Dns6   = @('2a13:1001::86:54:11:12', '2a13:1001::86:54:11:212')
$DohUrl = 'https://child.joindns4.eu/dns-query'
$PublicList = 'https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/gambling-only/hosts'
$PolicyKeys = @('HKLM:\SOFTWARE\Policies\Google\Chrome','HKLM:\SOFTWARE\Policies\Microsoft\Edge','HKLM:\SOFTWARE\Policies\BraveSoftware\Brave')

function Log($m) { Add-Content -Path $LogPath -Value ('{0:yyyy-MM-dd HH:mm:ss}  {1}' -f (Get-Date), $m) -Encoding ASCII }
function Read-Lines($name) {
  $p = Join-Path $Base $name
  if (-not (Test-Path $p)) { return @() }
  Get-Content $p | ForEach-Object { ($_ -replace '#.*$', '').Trim().ToLower() } | Where-Object { $_ }
}
function Is-Allowed($d, $allow) { foreach ($a in $allow) { if ($d -eq $a -or $d.EndsWith('.' + $a)) { return $true } }; $false }
function Get-Adapters {
  Get-NetAdapter -Physical -ErrorAction SilentlyContinue |
    Where-Object { $_.InterfaceDescription -notmatch 'Virtual|Hyper-V|VMware|Tailscale|TAP|WireGuard|Loopback' }
}
function Strip-Block($lines) {
  $out = New-Object System.Collections.Generic.List[string]; $skip = $false
  foreach ($l in $lines) {
    if ($l -eq $MarkStart) { $skip = $true; continue }
    if ($l -eq $MarkEnd) { $skip = $false; continue }
    if (-not $skip) { $out.Add($l) }
  }
  while ($out.Count -gt 0 -and $out[$out.Count-1].Trim() -eq '') { $out.RemoveAt($out.Count-1) }
  return ,$out
}
function Write-Hosts($out) {
  $tmp = "$HostsPath.fg.tmp"
  [System.IO.File]::WriteAllLines($tmp, $out, (New-Object System.Text.ASCIIEncoding))
  Copy-Item $tmp $HostsPath -Force; Remove-Item $tmp -Force
}

function Uninstall-All {
  Log 'UNINSTALL: cooldown finished, removing protection.'
  if (Test-Path $HostsPath) { Write-Hosts (Strip-Block (Get-Content $HostsPath)) }
  foreach ($a in Get-Adapters) { Set-DnsClientServerAddress -InterfaceIndex $a.ifIndex -ResetServerAddresses -ErrorAction SilentlyContinue }
  foreach ($ip in $Dns4 + $Dns6) { Remove-DnsClientDohServerAddress -ServerAddress $ip -ErrorAction SilentlyContinue }
  foreach ($k in $PolicyKeys) { Remove-ItemProperty $k -Name DnsOverHttpsMode -ErrorAction SilentlyContinue }
  Remove-Item 'HKLM:\SOFTWARE\Policies\Mozilla\Firefox\DNSOverHTTPS' -Recurse -ErrorAction SilentlyContinue
  Clear-DnsClientCache
  Unregister-ScheduledTask -TaskName 'FuckGambling' -Confirm:$false -ErrorAction SilentlyContinue
  Start-Process cmd.exe -ArgumentList "/c timeout /t 5 >nul & rmdir /s /q `"$Base`"" -WindowStyle Hidden
  exit 0
}

if (Test-Path $Request) {
  $t = [datetime]::MinValue
  if ([datetime]::TryParseExact((Get-Content $Request -TotalCount 1).Trim(), 'yyyy-MM-dd HH:mm:ss', $null, 'None', [ref]$t)) {
    $left = $t.AddHours($CooldownHours) - (Get-Date)
    if ($left.TotalSeconds -le 0) { Uninstall-All }
    Log ('Uninstall requested, {0:N1} h left. Protection stays on until then.' -f $left.TotalHours)
  } else { Remove-Item $Request -Force }
}

# ---- 1) block list -> hosts ----
$allow = @(Read-Lines 'allow.txt') + @(Read-Lines 'help-sites.txt')
$block = New-Object 'System.Collections.Generic.HashSet[string]'
try {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  $text = (New-Object Net.WebClient).DownloadString($PublicList)
  if (([regex]::Matches($text, '(?m)^0\.0\.0\.0 ')).Count -gt 1000) { Set-Content $Cache $text -Encoding ASCII }
} catch { Log ('List download failed, using cache: ' + $_.Exception.Message) }
if (Test-Path $Cache) {
  foreach ($l in Get-Content $Cache) { if ($l -match '^0\.0\.0\.0\s+([A-Za-z0-9\.\-]+)\s*$' -and $Matches[1] -ne '0.0.0.0') { [void]$block.Add($Matches[1].ToLower()) } }
}
foreach ($d in Read-Lines 'block.txt') { [void]$block.Add($d); [void]$block.Add('www.' + ($d -replace '^www\.', '')) }
foreach ($b in Read-Lines 'mirrors.txt') {
  foreach ($tld in 'com','net','org','tv','bet','vip','co','me','live','info','xyz','site','online','io') { [void]$block.Add("$b.$tld"); [void]$block.Add("www.$b.$tld") }
  foreach ($s in 'giris','girisi','guncel','guncelgiris','yenigiris','tv','mobil','bahis','casino','login') { [void]$block.Add("$b$s.com") }
  for ($i = 1; $i -le 1000; $i++) { [void]$block.Add("$b$i.com") }
}
$final = $block | Where-Object { -not (Is-Allowed $_ $allow) } | Sort-Object

# help sites: resolve through an unfiltered resolver and pin, so the DNS filter cannot hide them
$pins = New-Object System.Collections.Generic.List[string]
foreach ($h in Read-Lines 'help-sites.txt') {
  foreach ($name in @($h, "www.$h")) {
    try {
      $ip = (Resolve-DnsName $name -Server 9.9.9.9 -Type A -DnsOnly -QuickTimeout -ErrorAction Stop | Where-Object Type -eq 'A' | Select-Object -First 1).IPAddress
      if ($ip) { $pins.Add("$ip $name") }
    } catch {}
  }
}

try {
  $lines = if (Test-Path $HostsPath) { @(Get-Content $HostsPath) } else { @() }
  $out = Strip-Block $lines
  $out.Add(''); $out.Add($MarkStart)
  foreach ($p in $pins) { $out.Add($p) }
  foreach ($d in $final) { $out.Add("0.0.0.0 $d") }
  $out.Add($MarkEnd)
  if (($lines -join "`n") -cne ($out -join "`n")) { Write-Hosts $out; Log ("hosts updated: {0} blocked, {1} help pins." -f $final.Count, $pins.Count) }
} catch { Log ('hosts write failed: ' + $_.Exception.Message) }

# ---- 2) system DNS ----
# Another blocker (Gamban, BetBlocker, ...) that manages DNS itself would fight us every 30 min.
# In that case the hosts layer above stays on and DNS/browser settings are left to that blocker.
$other = Get-Service -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' -and $_.Name -match '^(Gamban|BetBlocker|GamBlock|BetFilter)' } | Select-Object -First 1
if ($other) {
  Log ("{0} is running and manages DNS - keeping hosts protection only." -f $other.Name)
  Clear-DnsClientCache
  return
}
foreach ($ip in $Dns4 + $Dns6) {
  try {
    if (Get-DnsClientDohServerAddress -ServerAddress $ip -ErrorAction SilentlyContinue) {
      Set-DnsClientDohServerAddress -ServerAddress $ip -DohTemplate $DohUrl -AllowFallbackToUdp $true -AutoUpgrade $true -ErrorAction Stop | Out-Null
    } else { Add-DnsClientDohServerAddress -ServerAddress $ip -DohTemplate $DohUrl -AllowFallbackToUdp $true -AutoUpgrade $true -ErrorAction Stop | Out-Null }
  } catch { Log ("DoH template failed ($ip): " + $_.Exception.Message) }
}
foreach ($a in Get-Adapters) {
  $cur = (Get-DnsClientServerAddress -InterfaceIndex $a.ifIndex -AddressFamily IPv4).ServerAddresses
  if (($cur -join ',') -ne ($Dns4 -join ',')) {
    try { Set-DnsClientServerAddress -InterfaceIndex $a.ifIndex -ServerAddresses ($Dns4 + $Dns6) -ErrorAction Stop; Log ("DNS set on {0} (was {1})" -f $a.Name, ($cur -join ',')) }
    catch { Log ("DNS failed on {0}: {1}" -f $a.Name, $_.Exception.Message) }
  }
}

# ---- 3) browsers must use system DNS ----
foreach ($k in $PolicyKeys) {
  if (-not (Test-Path $k)) { New-Item $k -Force | Out-Null }
  New-ItemProperty $k -Name DnsOverHttpsMode -Value 'off' -PropertyType String -Force | Out-Null
}
$ff = 'HKLM:\SOFTWARE\Policies\Mozilla\Firefox\DNSOverHTTPS'
if (-not (Test-Path $ff)) { New-Item $ff -Force | Out-Null }
New-ItemProperty $ff -Name Enabled -Value 0 -PropertyType DWord -Force | Out-Null
New-ItemProperty $ff -Name Locked -Value 1 -PropertyType DWord -Force | Out-Null

Clear-DnsClientCache
if ((Test-Path $LogPath) -and (Get-Item $LogPath).Length -gt 512KB) { Set-Content $LogPath (Get-Content $LogPath -Tail 2000) -Encoding ASCII }
