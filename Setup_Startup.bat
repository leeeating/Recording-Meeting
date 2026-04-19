@echo off
chcp 65001 >nul
title 會議錄製系統 - 自動啟動設定

:: 必須以系統管理員執行才能建立工作排程
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在要求系統管理員權限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: ================= 變數設定 =================
set "TASK_NAME=會議錄製後端"
set "BACKEND_BAT=%~dp0後端-會議記錄.bat"
set "FRONTEND_BAT=%~dp0前端-會議紀錄.bat"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
:: ============================================

echo.
echo [1/4] 建立工作排程「%TASK_NAME%」...
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%BACKEND_BAT%\"" ^
    /sc ONCE /st 00:00 /sd 01/01/2099 ^
    /rl highest ^
    /f

if %errorLevel% neq 0 (
    echo [錯誤] 工作排程建立失敗
    pause
    exit /b 1
)

echo.
echo [2/4] 建立 Startup 啟動捷徑...
powershell -Command ^
    "$s = New-Object -ComObject WScript.Shell; ^
     $sc = $s.CreateShortcut('%STARTUP_DIR%\會議錄製後端.lnk'); ^
     $sc.TargetPath = 'C:\Windows\System32\schtasks.exe'; ^
     $sc.Arguments = '/run /tn \"%TASK_NAME%\"'; ^
     $sc.WindowStyle = 7; ^
     $sc.Save()"

echo.
echo [3/4] 建立桌面後端捷徑「會議紀錄伺服器」...
powershell -Command ^
    "$s = New-Object -ComObject WScript.Shell; ^
     $sc = $s.CreateShortcut('%DESKTOP_DIR%\會議紀錄伺服器.lnk'); ^
     $sc.TargetPath = 'C:\Windows\System32\schtasks.exe'; ^
     $sc.Arguments = '/run /tn \"%TASK_NAME%\"'; ^
     $sc.WindowStyle = 7; ^
     $sc.Save()"

echo.
echo [4/4] 建立桌面前端捷徑「會議記錄管理介面」...
powershell -Command ^
    "$s = New-Object -ComObject WScript.Shell; ^
     $sc = $s.CreateShortcut('%DESKTOP_DIR%\會議記錄管理介面.lnk'); ^
     $sc.TargetPath = '%FRONTEND_BAT%'; ^
     $sc.WorkingDirectory = '%~dp0'; ^
     $sc.Save()"

echo.
echo 設定完成！
echo.
echo  工作排程：%TASK_NAME%
echo  Startup 捷徑：%STARTUP_DIR%\會議錄製後端.lnk
echo  桌面後端捷徑：%DESKTOP_DIR%\會議紀錄伺服器.lnk
echo  桌面前端捷徑：%DESKTOP_DIR%\會議記錄管理介面.lnk
echo.
pause
