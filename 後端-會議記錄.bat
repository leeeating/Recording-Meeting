@echo off
title 會議記錄-後端伺服器
:: 檢查是否具有管理員權限
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :admin
) else (
    echo 正在要求系統管理員權限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:admin
cd /d "C:\Users\linlab\Documents\Recording-Meeting"

echo [%date% %time%] 啟動後端伺服器 >> logs\backend\startup.log
uv run uvicorn app.main:app
echo [%date% %time%] 後端伺服器已停止 (exit code: %errorlevel%) >> logs\backend\startup.log

pause