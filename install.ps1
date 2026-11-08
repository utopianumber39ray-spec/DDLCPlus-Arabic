# DDLC+ Arabic Patch - installer (Windows PowerShell 5+)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$src  = Join-Path $root 'files'
$exeName = 'Doki Doki Literature Club Plus.exe'
$files = @(
  'Doki Doki Literature Club Plus_Data\Managed\DDLC.dll',
  'Doki Doki Literature Club Plus_Data\Managed\ArabicShaper.dll',
  'Doki Doki Literature Club Plus_Data\sharedassets1.assets',
  'Doki Doki Literature Club Plus_Data\sharedassets2.assets',
  'Doki Doki Literature Club Plus_Data\resources.assets',
  'Doki Doki Literature Club Plus_Data\StreamingAssets\AssetBundles\Windows\langar.cy',
  'Doki Doki Literature Club Plus_Data\StreamingAssets\AssetBundles\Windows\gui.cy',
  'Doki Doki Literature Club Plus_Data\StreamingAssets\AssetBundles\Windows\supportedlanguages.cy'
)

Write-Host ''
Write-Host '============================================================'
Write-Host '  DDLC+ Arabic Localization Patch - Installer'
Write-Host '============================================================'
Write-Host ''

if (-not (Test-Path -LiteralPath $src)) {
  Write-Host 'ERROR: the "files" folder is missing next to this script.' -ForegroundColor Red
  exit 1
}

if (Get-Process -Name 'Doki Doki Literature Club Plus' -ErrorAction SilentlyContinue) {
  Write-Host 'ERROR: the game is running. Close it and run the installer again.' -ForegroundColor Red
  exit 1
}

function Find-Game([string]$path) {
  if ([string]::IsNullOrWhiteSpace($path)) { return $null }
  $p = $path.Trim().Trim('"')
  if (Test-Path -LiteralPath (Join-Path $p $exeName)) { return $p }
  return $null
}

$candidates = New-Object System.Collections.Generic.List[string]
$steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
if ($steam) {
  $steam = $steam -replace '/', '\'
  $candidates.Add((Join-Path $steam 'steamapps\common\Doki Doki Literature Club Plus'))
  $vdf = Join-Path $steam 'steamapps\libraryfolders.vdf'
  if (Test-Path -LiteralPath $vdf) {
    foreach ($line in Get-Content -LiteralPath $vdf) {
      if ($line -match '"path"\s+"(.+?)"') {
        $lib = $matches[1] -replace '\\\\', '\'
        $candidates.Add((Join-Path $lib 'steamapps\common\Doki Doki Literature Club Plus'))
      }
    }
  }
}
$candidates.Add('C:\Program Files (x86)\Steam\steamapps\common\Doki Doki Literature Club Plus')
$candidates.Add('C:\Program Files\Steam\steamapps\common\Doki Doki Literature Club Plus')

$game = $null
foreach ($c in $candidates) {
  $g = Find-Game $c
  if ($g) { $game = $g; break }
}

if (-not $game) {
  Write-Host 'The game folder was not detected automatically.'
  Write-Host 'Paste the full path to the folder that contains "Doki Doki Literature Club Plus.exe"'
  Write-Host 'Example: C:\Program Files (x86)\Steam\steamapps\common\Doki Doki Literature Club Plus'
  Write-Host ''
  $answer = Read-Host 'Game folder'
  $game = Find-Game $answer
  if (-not $game) {
    Write-Host 'ERROR: "Doki Doki Literature Club Plus.exe" was not found in that folder.' -ForegroundColor Red
    exit 1
  }
}

Write-Host ''
Write-Host ('Game folder: ' + $game)
Write-Host ''

$bk = Join-Path $game '_DDLCPlus_Arabic_Backup'
New-Item -ItemType Directory -Force -Path $bk | Out-Null
$absent = @()

Write-Host '[1/2] Backing up original files...'
foreach ($rel in $files) {
  $dest = Join-Path $game $rel
  $back = Join-Path $bk $rel
  if (Test-Path -LiteralPath $dest) {
    if (-not (Test-Path -LiteralPath $back)) {
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $back) | Out-Null
      Copy-Item -LiteralPath $dest -Destination $back -Force
    }
  } else {
    $absent += $rel
  }
}
if ($absent.Count -gt 0) {
  Set-Content -LiteralPath (Join-Path $bk 'absent.txt') -Value $absent -Encoding UTF8
}

Write-Host '[2/2] Installing Arabic files...'
$dllRel = 'Doki Doki Literature Club Plus_Data\Managed\DDLC.dll'
$origDll = 'FFE9C000E5530AE6AE7A15B48DD255FAC837EC9B7D1D5163DBC2562CFA5F2CE1'
$patchedDll = '94677D4623C51D79E6BE3D63FC26566B4C3D2A6AFBEB42D6ED6988CB0E36DFDE'
foreach ($rel in $files) {
  $s = Join-Path $src $rel
  $d = Join-Path $game $rel
  if (-not (Test-Path -LiteralPath $s)) {
    Write-Host ('ERROR: missing patch file: ' + $rel) -ForegroundColor Red
    exit 1
  }
  if ($rel -eq $dllRel -and (Test-Path -LiteralPath $d)) {
    $h = (Get-FileHash -LiteralPath $d -Algorithm SHA256).Hash
    if ($h -ne $origDll -and $h -ne $patchedDll) {
      Write-Host '  WARNING: your DDLC.dll is from a different game build; keeping it.' -ForegroundColor Yellow
      Write-Host '           The language name may appear as "MISSING!" in the list, but Arabic will still work.' -ForegroundColor Yellow
      continue
    }
  }
  Copy-Item -LiteralPath $s -Destination $d -Force
  Write-Host ('  ok: ' + $rel)
}

Write-Host ''
Write-Host '============================================================'
Write-Host '  Done. The Arabic localization is installed.'
Write-Host ''
Write-Host '  The game now starts in Arabic automatically (first launch included).'
Write-Host '  You can change the language any time from Settings -> Language.'
Write-Host '  To remove it, run restore.bat'
Write-Host '============================================================'
Write-Host ''
Read-Host 'Press Enter to exit'
exit 0
