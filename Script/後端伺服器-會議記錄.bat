@echo off
:: 1. 權限檢查與提升 (維持你的邏輯)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在要求系統管理員權限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 2. 【關鍵】動態切換到腳本所在的目錄
:: 不管專案在 Documents、OneDrive 還是 D 槽，也不管資料夾叫什麼名字
:: %~dp0 永遠代表「此腳本所在的資料夾」
cd /d "%~dp0"

:: 3. 確保環境同步 (建議執行前順便 sync，防呆)
uv sync

:: 4. 執行
echo [啟動] 正在啟動 Fast API 伺服器...
uv run uvicorn app.main:app --reload

pause