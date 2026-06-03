#!/bin/bash
# QuantEvo 停止脚本

echo "🛑 Stopping QuantEvo services..."

# Kill backend
BACKEND_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$BACKEND_PID" ]; then
    echo "  📡 Stopping backend (PID: $BACKEND_PID)"
    kill $BACKEND_PID 2>/dev/null
    sleep 1
fi

# Kill frontend
FRONTEND_PID=$(lsof -ti:3000 2>/dev/null)
if [ -n "$FRONTEND_PID" ]; then
    echo "  🎨 Stopping frontend (PID: $FRONTEND_PID)"
    kill $FRONTEND_PID 2>/dev/null
    sleep 1
fi

echo ""
echo "✅ All services stopped"
