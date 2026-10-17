@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Patch.ps1" -Mode Check
pause
