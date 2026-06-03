#!/bin/bash
# QuantEvo 启动脚本 - 启动前后端服务

cd "$(dirname "$0")"

echo "🚀 Starting QuantEvo services..."

# Start backend
cd backend
if ! lsof -ti:8000 > /dev/null 2>&1; then
    echo "  📡 Starting backend on :8000"
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
else
    echo "  📡 Backend already running on :8000"
fi

# Start frontend
cd ../frontend
if ! lsof -ti:3000 > /dev/null 2>&1; then
    echo "  🎨 Starting frontend on :3000"
    nohup npx vite --port 3000 --host > ../logs/frontend.log 2>&1 &
else
    echo "  🎨 Frontend already running on :3000"
fi

echo ""
echo "✅ Services started:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "📋 Logs: ./logs/"
echo "🛑 Stop:  ./stop-all.sh"
