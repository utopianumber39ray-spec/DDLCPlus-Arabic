# DDLC+ Arabic Patch - restore original files
$ErrorActionPreference = 'Stop'
$exeName = 'Doki Doki Literature Club Plus.exe'

Write-Host ''
Write-Host '============================================================'
Write-Host '  DDLC+ Arabic Patch - Restore original files'
Write-Host '============================================================'
Write-Host ''

if (Get-Process -Name 'Doki Doki Literature Club Plus' -ErrorAction SilentlyContinue) {
  Write-Host 'ERROR: the game is running. Close it first.' -ForegroundColor Red
  exit 1
}

$answer = Read-Host 'Game folder (leave empty for the default Steam path)'
$answer = $answer.Trim().Trim('"')
if ([string]::IsNullOrWhiteSpace($answer)) {
  $answer = 'C:\Program Files (x86)\Steam\steamapps\common\Doki Doki Literature Club Plus'
}
if (-not (Test-Path -LiteralPath (Join-Path $answer $exeName))) {
  Write-Host ('ERROR: game folder not found: ' + $answer) -ForegroundColor Red
  exit 1
}
$game = $answer
$bk = Join-Path $game '_DDLCPlus_Arabic_Backup'
if (-not (Test-Path -LiteralPath $bk)) {
  Write-Host ('ERROR: no backup found at ' + $bk) -ForegroundColor Red
  exit 1
}

Write-Host 'Restoring...'
Get-ChildItem -LiteralPath $bk -Recurse -File | ForEach-Object {
  if ($_.Name -ne 'absent.txt') {
    $rel = $_.FullName.Substring($bk.Length).TrimStart('\')
    $dest = Join-Path $game $rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $dest -Force
    Write-Host ('  restored: ' + $rel)
  }
}
$absentFile = Join-Path $bk 'absent.txt'
if (Test-Path -LiteralPath $absentFile) {
  foreach ($rel in Get-Content -LiteralPath $absentFile) {
    if ([string]::IsNullOrWhiteSpace($rel)) { continue }
    $dest = Join-Path $game $rel
    if (Test-Path -LiteralPath $dest) {
      Remove-Item -LiteralPath $dest -Force
      Write-Host ('  removed: ' + $rel)
    }
  }
}

Write-Host 'Done. Original files restored.'
Read-Host 'Press Enter to exit'
exit 0
