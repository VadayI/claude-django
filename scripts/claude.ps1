#!/usr/bin/env pwsh
# Child-only environment; preserve argv and exit code without changing caller vars.
$ErrorActionPreference = 'Stop'
$launcherRoot = Split-Path -Parent $PSScriptRoot
$launcherPython = if ($env:AI_PYTHON) { $env:AI_PYTHON } else { 'python' }
& $launcherPython (Join-Path $PSScriptRoot 'ai/legacy_launch.py') claude --root $launcherRoot -- @args
exit $LASTEXITCODE
