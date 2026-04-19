@echo off
cd C:\Users\linlab\Documents\Recording-Meeting
powershell -windowstyle hidden -command "Start-Process uv -ArgumentList 'run pythonw -m frontend.UI' -WindowStyle Hidden"
exit