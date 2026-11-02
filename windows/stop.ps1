# Turns off automatic moving completely. A manual "Move now" still works.
. (Join-Path $PSScriptRoot 'common.ps1')

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
New-Item -ItemType File -Force (Join-Path $ToolDir 'PAUSE') | Out-Null
Write-Host 'Desktop to Drive is OFF'
