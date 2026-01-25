@echo off
cd /d "%~dp0"

echo [1/2] 正在獲取遠端更新並進行 Rebase...

:: 1. 抓取遠端最新狀態 (不影響本地檔案)
git fetch origin

:: 2. 強制切換到 main 分支 (預防使用者目前在奇怪的分支)
git checkout main

:: 3. 執行 Rebase
:: 這會把本地的修改「墊」在遠端最新進度之上
git rebase origin/main

if %errorlevel% neq 0 (
    echo [警告] Rebase 發生衝突！請手動解決衝突，或執行 git rebase --abort 取消。
    pause
    exit /b 1
)

:: 4. 同步 Python 環境
echo [2/2] 更新依賴套件 (uv sync)...
uv sync

echo ---------------------------------------
echo 更新完成！
echo ---------------------------------------
pause