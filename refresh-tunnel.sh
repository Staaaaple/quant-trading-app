#!/bin/bash
# QuantEvo 公网隧道一键刷新脚本（Git Bash 版）

URL_FILE="d:/quant_app/quant-trading-app/.claude/tunnel/current_url.txt"
OUTFILE="/tmp/lt_url_$$.txt"
PORT=8001

mkdir -p "$(dirname "$URL_FILE")"

echo "========================================"
echo "  QuantEvo 公网隧道一键刷新"
echo "========================================"
echo ""

# 1. 检查后端
echo "[1/4] 检查后端服务 http://127.0.0.1:$PORT ..."
if ! curl -s --max-time 5 "http://127.0.0.1:$PORT/health" >/dev/null; then
    echo ""
    echo "[x] 后端没有启动！请先启动后端："
    echo ""
    echo "    cd d:/quant_app/quant-trading-app/backend"
    echo "    C:/Users/Alienware/.conda/envs/quant/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi
echo "[ok] 后端运行正常。"
echo ""

# 2. 关闭旧 tunnel
echo "[2/4] 关闭旧的 localtunnel 进程..."
for pid in $(wmic process where "CommandLine like '%localtunnel%--port $PORT%'" get ProcessId /value 2>/dev/null | grep -o '[0-9]*'); do
    taskkill //F //PID "$pid" >/dev/null 2>&1
done
sleep 2
echo "[ok] 已清理。"
echo ""

# 3. 启动新 tunnel
echo "[3/4] 启动新的 localtunnel ..."
npx localtunnel --port $PORT > "$OUTFILE" 2>&1 &
LT_PID=$!

# 4. 等待并提取 URL
echo "[4/4] 等待 tunnel 地址生成..."
URL=""
for i in {1..30}; do
    sleep 1
    URL=$(grep -oE 'https://[a-z0-9-]+\.loca\.lt' "$OUTFILE" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
        break
    fi
done

if [ -z "$URL" ]; then
    echo ""
    echo "[x] 获取 tunnel 地址超时。"
    echo "    输出日志: $OUTFILE"
    read -p "按回车键退出..."
    exit 1
fi

echo "$URL" > "$URL_FILE"

echo ""
echo "========================================"
echo "  新地址: $URL"
echo "========================================"
echo ""

# 5. 尝试打开浏览器
start "$URL" 2>/dev/null || explorer "$URL" 2>/dev/null || echo "请手动复制地址到浏览器打开。"

echo "已尝试用浏览器打开。"
echo "提示：把这个地址发给其他人，他们就能访问你的项目。"
echo "      如果之后打不开了，重新运行这个脚本即可。"
read -p "按回车键退出..."
