@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PORT=8001"
set "OUTFILE=%TEMP%\lt_url.txt"

REM 关掉旧 localtunnel
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

REM 启动新 tunnel
if exist "%OUTFILE%" del "%OUTFILE%" >nul 2>&1
start /MIN cmd /c "npx localtunnel --port %PORT% > ""%OUTFILE%"" 2>&1"

REM 等待并提取 URL
for /L %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    if exist "%OUTFILE%" (
        for /f "delims=" %%a in ('powershell -Command "if (Test-Path '%OUTFILE%') { $c = Get-Content '%OUTFILE%' -Raw; if ($c -match 'https://[a-z0-9-]+\.loca\.lt') { $matches[0] } }"') do (
            echo %%a
            exit /b 0
        )
    )
)

echo 获取 tunnel 地址失败
exit /b 1
