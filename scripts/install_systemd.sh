#!/bin/bash
#
# Install STCI systemd services
#
# Usage:
#   sudo ./scripts/install_systemd.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SYSTEMD_DIR="/etc/systemd/system"

echo "=== STCI Systemd Installation ==="
echo "Project: ${PROJECT_ROOT}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (sudo)"
    exit 1
fi

# Create logs directory
mkdir -p "${PROJECT_ROOT}/logs"
chown jeremy:jeremy "${PROJECT_ROOT}/logs"

# Copy service files
echo "Installing systemd units..."
cp "${SCRIPT_DIR}/systemd/stci-daily.service" "${SYSTEMD_DIR}/"
cp "${SCRIPT_DIR}/systemd/stci-daily.timer" "${SYSTEMD_DIR}/"
cp "${SCRIPT_DIR}/systemd/stci-api.service" "${SYSTEMD_DIR}/"

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable timer (not service - timer triggers service)
echo "Enabling stci-daily timer..."
systemctl enable stci-daily.timer
systemctl start stci-daily.timer

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Timer status:"
systemctl status stci-daily.timer --no-pager || true
echo ""
echo "Next scheduled run:"
systemctl list-timers stci-daily.timer --no-pager || true
echo ""
echo "Commands:"
echo "  systemctl status stci-daily.timer   # Check timer status"
echo "  systemctl start stci-daily.service  # Run pipeline now"
echo "  journalctl -u stci-daily.service    # View logs"
echo ""
echo "To enable the API server:"
echo "  systemctl enable --now stci-api.service"
echo "  systemctl status stci-api.service"
echo ""
