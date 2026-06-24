#!/bin/bash
# 维护 localtunnel 连接

PORT=8001
URL_FILE="d:/quant_app/quant-trading-app/.claude/tunnel/current_url.txt"
LOG_FILE="d:/quant_app/quant-trading-app/.claude/tunnel/maintain.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

start_tunnel() {
  log "启动新隧道..."
  # 清理已有 localtunnel 进程
  for pid in $(wmic process where "CommandLine like '%localtunnel%--port $PORT%'" get ProcessId /value 2>/dev/null | grep -o '[0-9]*'); do
    taskkill //F //PID "$pid" >/dev/null 2>&1
  done
  
  # 启动新隧道，输出到临时文件
  TMP_OUT=$(mktemp)
  npx localtunnel --port $PORT > "$TMP_OUT" 2>&1 &
  LT_PID=$!
  
  # 等待 URL 出现
  for i in {1..30}; do
    URL=$(grep -oE 'https://[a-z0-9-]+\.loca\.lt' "$TMP_OUT" | head -1)
    if [ -n "$URL" ]; then
      echo "$URL" > "$URL_FILE"
      log "隧道已启动: $URL (PID: $LT_PID)"
      rm -f "$TMP_OUT"
      return 0
    fi
    sleep 1
  done
  
  log "启动隧道超时"
  rm -f "$TMP_OUT"
  return 1
}

# 首次启动
start_tunnel

# 每 5 分钟检查一次
while true; do
  sleep 300
  CURRENT_URL=$(cat "$URL_FILE" 2>/dev/null)
  if [ -z "$CURRENT_URL" ]; then
    log "URL 文件为空，重新启动隧道"
    start_tunnel
    continue
  fi
  
  if ! curl -s --max-time 8 "$CURRENT_URL/health" >/dev/null 2>&1; then
    log "隧道 $CURRENT_URL 不可达，重新启动"
    start_tunnel
  else
    log "隧道 $CURRENT_URL 正常"
  fi
done
