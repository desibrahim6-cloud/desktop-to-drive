# Shared helpers for the Windows scripts (ASCII only: Windows PowerShell 5.1 reads scripts as ANSI).
$TaskName = 'DesktopToDrive'
$ToolDir = $PSScriptRoot
$MoveScript = Join-Path $ToolDir 'move.py'

function Find-Python {
    # Returns python.exe (with a console) and pythonw.exe (no window, for Task Scheduler).
    foreach ($cmd in @('py', 'python')) {
        $a = @('-c', 'import sys; print(sys.executable)')
        if ($cmd -eq 'py') { $a = @('-3') + $a }
        try { $exe = (& $cmd @a 2>$null | Select-Object -First 1) } catch { continue }
        if ($exe -and (Test-Path $exe)) {
            $w = Join-Path (Split-Path $exe) 'pythonw.exe'
            if (-not (Test-Path $w)) { $w = $exe }
            return @{ Console = $exe; NoWindow = $w }
        }
    }
    throw "Python 3 not found. Install it free from python.org (tick 'Add python.exe to PATH'), then try again."
}

function Test-AutoOn {
    return [bool](Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)
}
