# Turns on automatic moving: Task Scheduler runs move.py every hour while you are signed in.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')

$py = Find-Python
$action = New-ScheduledTaskAction -Execute $py.NoWindow -Argument "`"$MoveScript`"" -WorkingDirectory $ToolDir
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Description 'Desktop to Drive: moves old Desktop items to Google Drive every hour' -Force | Out-Null
Remove-Item (Join-Path $ToolDir 'PAUSE') -ErrorAction SilentlyContinue
Write-Host 'Desktop to Drive is ON'
