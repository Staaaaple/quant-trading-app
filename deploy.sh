#!/bin/bash
# QuantEvo Deployment Script
# Usage: ./deploy.sh [dev|prod]

set -e

ENV=${1:-prod}
COMPOSE_FILE="docker-compose.yml"

echo "═══════════════════════════════════════════════════════════════"
echo "  QuantEvo Deployment Script"
echo "  Environment: $ENV"
echo "═══════════════════════════════════════════════════════════════"

# ── Check dependencies ──
command -v docker >/dev/null 2>&1 || { echo "Error: Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Error: docker-compose is required but not installed."; exit 1; }

# ── Create necessary directories ──
echo "[1/6] Creating directories..."
mkdir -p backend/data backend/logs backend/data_cache
mkdir -p frontend/dist

# ── Stop existing containers ──
echo "[2/6] Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down --remove-orphans 2>/dev/null || true

# ── Build images ──
echo "[3/6] Building Docker images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# ── Start services ──
echo "[4/6] Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# ── Wait for backend health ──
echo "[5/6] Waiting for backend to be healthy..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo "  ✓ Backend is healthy"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# ── Verify deployment ──
echo "[6/6] Verifying deployment..."
echo ""
echo "  Services Status:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "  Health Checks:"
echo -n "  Backend API: "
curl -sf http://localhost:8000/health && echo "✓ OK" || echo "✗ FAILED"

echo -n "  Frontend:    "
curl -sf http://localhost:80/health && echo "✓ OK" || echo "✗ FAILED"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Deployment Complete!"
echo ""
echo "  Frontend: http://localhost"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/api/v1/docs"
echo ""
echo "  Useful commands:"
echo "    View logs:    docker-compose logs -f"
echo "    Stop:         docker-compose down"
echo "    Restart:      docker-compose restart"
echo "    Update:       docker-compose pull && docker-compose up -d"
echo "═══════════════════════════════════════════════════════════════"
