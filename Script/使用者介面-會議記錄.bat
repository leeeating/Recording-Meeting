@echo off
:: 1. 定位腳本所在路徑（以專案為中心）
cd /d "%~dp0"

:: 2. 使用 PowerShell 啟動靜默進程
:: 使用 pythonw 確保沒有 python 的黑視窗
:: 使用 -WindowStyle Hidden 確保啟動瞬間的視窗也被隱藏
powershell -WindowStyle Hidden -Command "Start-Process uv -ArgumentList 'run pythonw -m frontend.UI' -WindowStyle Hidden"

:: 3. 立即結束批次檔視窗
exit