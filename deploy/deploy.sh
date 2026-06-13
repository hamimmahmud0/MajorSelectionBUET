#!/usr/bin/env bash
# ============================================================
# Deploy script for BUET Major Selection System
# ============================================================
# This script sets up the production environment.
# Run it ONCE after cloning the repo on the server.
#
# Usage:
#   chmod +x deploy/deploy.sh
#   ./deploy/deploy.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="buet-major-selection"

echo "========================================"
echo "  Deploying: $SERVICE_NAME"
echo "  Directory: $PROJECT_DIR"
echo "========================================"

# ─── Step 1: Create instance directory for DB ───
mkdir -p "$PROJECT_DIR/instance"
echo "[✓] Instance directory ready"

# ─── Step 2: Install / update Python dependencies ───
echo "[...] Installing Python dependencies..."
cd "$PROJECT_DIR"
pip install -r requirements.txt --quiet
echo "[✓] Dependencies installed"

# ─── Step 3: Copy systemd service file (requires sudo) ───
SERVICE_SRC="$PROJECT_DIR/deploy/$SERVICE_NAME.service"
SERVICE_DST="/etc/systemd/system/$SERVICE_NAME.service"

if [ ! -f "$SERVICE_DST" ]; then
    echo "[...] Installing systemd service (sudo required)..."
    sudo cp "$SERVICE_SRC" "$SERVICE_DST"
    sudo systemctl daemon-reload
    echo "[✓] Systemd service installed"
else
    echo "[✓] Systemd service already exists — skipping (update manually if needed)"
fi

# ─── Step 4: Enable and start the service ───
echo "[...] Enabling and starting service..."
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
echo "[✓] Service started"

# ─── Step 5: Show status ───
echo ""
echo "========================================"
echo "  Deployment complete!"
echo "========================================"
echo ""
echo "  Check status:  sudo systemctl status $SERVICE_NAME"
echo "  View logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart:       sudo systemctl restart $SERVICE_NAME"
echo "  Stop:          sudo systemctl stop $SERVICE_NAME"
echo ""

# ─── Step 6: Quick health check ───
sleep 2
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "[✓] Service is running!"
else
    echo "[!] Service failed to start. Check: sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
fi
