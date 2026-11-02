@echo off
rem Installs Desktop to Drive into %USERPROFILE%\DesktopToDrive and adds it to the Start menu.
rem Automatic moving stays OFF until you choose "Turn on" in the menu.
setlocal
set "DEST=%USERPROFILE%\DesktopToDrive"
if not exist "%DEST%" mkdir "%DEST%"
copy /Y "%~dp0..\move.py" "%DEST%\" >nul
copy /Y "%~dp0common.ps1" "%DEST%\" >nul
copy /Y "%~dp0start.ps1" "%DEST%\" >nul
copy /Y "%~dp0stop.ps1" "%DEST%\" >nul
copy /Y "%~dp0menu.ps1" "%DEST%\" >nul
copy /Y "%~dp0Desktop to Drive.bat" "%DEST%\" >nul
if not exist "%DEST%\keep.txt" echo # Names of Desktop items to keep (one per line)> "%DEST%\keep.txt"
schtasks /Query /TN DesktopToDrive >nul 2>&1 || type nul > "%DEST%\PAUSE"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Programs')+'\Desktop to Drive.lnk'); $s.TargetPath='%DEST%\Desktop to Drive.bat'; $s.WorkingDirectory='%DEST%'; $s.Save()"
echo Installed in %DEST%
echo Open "Desktop to Drive" from the Start menu.
pause
