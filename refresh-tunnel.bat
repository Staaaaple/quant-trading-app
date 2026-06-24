@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   QuantEvo 公网隧道一键刷新脚本
echo ========================================
echo.

set "URL_FILE=d:\quant_app\quant-trading-app\.claude\tunnel\current_url.txt"
set "OUTFILE=%TEMP%\lt_url.txt"

REM 1. 检查后端是否运行
echo [1/4] 检查后端服务 http://127.0.0.1:8001 ...
curl -s --max-time 5 http://127.0.0.1:8001/health >nul
if errorlevel 1 (
    echo.
    echo [x] 后端没有启动！请先启动后端：
    echo.
    echo     cd d:\quant_app\quant-trading-app\backend
    echo     C:\Users\Alienware\.conda\envs\quant\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 1
    echo.
    pause
    exit /b 1
)
echo [ok] 后端运行正常。
echo.

REM 2. 关闭旧 tunnel
echo [2/4] 关闭旧的 localtunnel 进程...
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo [ok] 已清理。
echo.

REM 3. 启动新 tunnel
echo [3/4] 启动新的 localtunnel ...
if exist "%OUTFILE%" del "%OUTFILE%" >nul 2>&1
if not exist "d:\quant_app\quant-trading-app\.claude\tunnel" mkdir "d:\quant_app\quant-trading-app\.claude\tunnel" >nul 2>&1

start /MIN cmd /c "npx localtunnel --port 8001 > ""%OUTFILE%"" 2>&1"

REM 4. 等待并提取 URL
echo [4/4] 等待 tunnel 地址生成...
set "URL="
for /L %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    if exist "%OUTFILE%" (
        for /f "delims=" %%a in ('powershell -Command "if (Test-Path ''%OUTFILE%'') { $c = Get-Content ''%OUTFILE%'' -Raw; if ($c -match ''https://[a-z0-9-]+\.loca\.lt'') { $matches[0] } }"') do (
            set "URL=%%a"
            goto :found
        )
    )
)

if "!URL!"=="" (
    echo.
    echo [x] 获取 tunnel 地址超时，请查看输出文件：%OUTFILE%
    pause
    exit /b 1
)

:found
echo !URL! > "%URL_FILE%"
echo.
echo ========================================
echo   新地址: !URL!
echo ========================================
echo.

REM 5. 用默认浏览器打开
start "" "!URL!"
echo 已尝试用浏览器打开。
echo.
echo 提示：把这个地址发给其他人，他们就能访问你的项目。
echo      如果之后打不开了，再双击运行这个脚本即可。
pause
