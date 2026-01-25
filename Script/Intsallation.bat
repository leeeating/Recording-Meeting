@echo off
setlocal enabledelayedexpansion
title 一鍵安裝工具

:: --- 設定區 ---
set "REPOS_URL=https://github.com/leeeating/Recording-Meeting.git"
set "PROJECT_NAME=Recording-Meeting"
:: 定位到 Windows 文件資料夾
set "TARGET_DIR=%USERPROFILE%\Documents"
:: --------------

:: 1. 檢查 Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [錯誤] 找不到 Git，請先安裝 Git。
    pause
    exit /b 1
)

:: 2. 切換到文件資料夾
cd /d "%TARGET_DIR%"
echo [資訊] 準備在 %TARGET_DIR% 安裝專案...

:: 3. 執行 Clone
if exist "%PROJECT_NAME%" (
    echo [警告] 資料夾 %PROJECT_NAME% 已存在，跳過 Clone 步驟。
    cd /d "%PROJECT_NAME%"
) else (
    echo [1/3] 正在從 GitHub 下載專案...
    git clone %REPOS_URL% "%PROJECT_NAME%"
    if %errorlevel% neq 0 (
        echo [錯誤] Clone 失敗，請檢查網址或網路。
        pause
        exit /b 1
    )
    cd /d "%PROJECT_NAME%"
)

:: 4. 檢查並安裝 uv
echo [2/3] 正在檢查 uv 環境...
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [提示] 未偵測到 uv，正在安裝...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)

:: 5. 同步環境
echo [3/3] 正在同步 Python 環境 (uv sync)...
uv sync

echo ---------------------------------------
echo [成功] 專案已安裝於: %cd%
echo 現在你可以執行程式了。
echo ---------------------------------------
pause