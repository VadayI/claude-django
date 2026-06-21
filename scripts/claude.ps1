#!/usr/bin/env pwsh
# scripts/claude.ps1 — launch Claude Code with the project .env sourced (PowerShell).
#
# WHY: Claude Code does NOT auto-load a project .env, and ${VAR} in .mcp.json
# (plus the github/context7 plugins) resolves from the process environment that
# launched `claude`. Launch Claude through this wrapper so every variable in .env
# reaches the MCP servers, the gh CLI, and the tooling WITHOUT setting anything
# permanently in your user environment. Never prints secret values. .env stays gitignored.
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $Root '.env'

$names = 'CONTRACT_REPO','CONTRACT_VERSION','GITHUB_PERSONAL_ACCESS_TOKEN','CONTEXT7_API_KEY'

# Snapshot pre-existing env so an EMPTY placeholder in .env can't clobber it.
$pre = @{}
foreach ($name in $names) { $pre[$name] = [Environment]::GetEnvironmentVariable($name) }

if (Test-Path $EnvFile) {
  foreach ($line in Get-Content -LiteralPath $EnvFile) {
    $t = $line.Trim()
    if ($t -eq '' -or $t.StartsWith('#')) { continue }
    $idx = $t.IndexOf('=')
    if ($idx -lt 1) { continue }
    $key = $t.Substring(0, $idx).Trim()
    $val = $t.Substring($idx + 1).Trim()
    if ($val.Length -ge 2 -and (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'")))) {
      $val = $val.Substring(1, $val.Length - 2)
    }
    Set-Item -Path "Env:$key" -Value $val
  }
}

# .env wins when filled; otherwise fall back to what was already in the shell.
foreach ($name in $names) {
  $cur = [Environment]::GetEnvironmentVariable($name)
  if ([string]::IsNullOrEmpty($cur) -and -not [string]::IsNullOrEmpty($pre[$name])) {
    Set-Item -Path "Env:$name" -Value $pre[$name]
  }
}

# gh authenticates with GH_TOKEN, then GITHUB_TOKEN — not GITHUB_PERSONAL_ACCESS_TOKEN.
# A PAT in .env is authoritative for gh: copy it into GH_TOKEN (overriding any inherited,
# often-stale system GH_TOKEN) and drop any inherited GITHUB_TOKEN.
if (-not [string]::IsNullOrEmpty($env:GITHUB_PERSONAL_ACCESS_TOKEN)) {
  $env:GH_TOKEN = $env:GITHUB_PERSONAL_ACCESS_TOKEN
  Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue
}

claude @args
exit $LASTEXITCODE
