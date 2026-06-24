#!/bin/bash
# 刷新 localtunnel 并输出新地址（Git Bash）

PORT=8001
OUTFILE="/tmp/lt_url_$$.txt"

# 杀掉旧 tunnel
for pid in $(wmic process where "CommandLine like '%localtunnel%--port $PORT%'" get ProcessId /value 2>/dev/null | grep -o '[0-9]*'); do
  taskkill //F //PID "$pid" >/dev/null 2>&1
done
sleep 2

# 启动新 tunnel
npx localtunnel --port $PORT > "$OUTFILE" 2>&1 &

# 提取 URL
for i in {1..30}; do
  sleep 1
  URL=$(grep -oE 'https://[a-z0-9-]+\.loca\.lt' "$OUTFILE" 2>/dev/null | head -1)
  if [ -n "$URL" ]; then
    echo "$URL"
    exit 0
  fi
done

echo "获取 tunnel 地址失败"
exit 1
