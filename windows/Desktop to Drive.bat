@echo off
rem Double-click to open the Desktop to Drive window.
start "" powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0menu.ps1"
