#!/bin/bash

# MyRepublic Evil Twin Portal - Dependencies Installer
# Script ini akan menginstall semua dependencies yang diperlukan

echo "🚀 Installing MyRepublic Evil Twin Portal Dependencies..."
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Update package list
echo "📦 Updating package list..."
apt update

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt install -y python3 python3-pip python3-venv hostapd-mana dnsmasq iptables iwconfig

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install fastapi uvicorn python-multipart

# Create virtual environment (optional)
echo "📁 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn python-multipart

# Check WiFi interface
echo "📡 Checking WiFi interface..."
if iwconfig 2>/dev/null | grep -q wlan0; then
    echo "✅ WiFi interface wlan0 found"
else
    echo "⚠️  WiFi interface wlan0 not found"
    echo "   Available interfaces:"
    iwconfig 2>/dev/null || echo "   No wireless interfaces found"
fi

# Check internet interface
echo "🌐 Checking internet interface..."
if ip link show eth0 >/dev/null 2>&1; then
    echo "✅ Internet interface eth0 found"
else
    echo "⚠️  Internet interface eth0 not found"
    echo "   Available interfaces:"
    ip link show | grep -E "^[0-9]+:"
fi

# Set permissions
echo "🔐 Setting file permissions..."
chmod +x evil_twin_portal.py
chmod 644 evil.conf

# Create log directory
echo "📝 Creating log directory..."
mkdir -p logs

echo ""
echo "✅ Installation completed!"
echo "=================================================="
echo "📋 Next steps:"
echo "1. Edit evil.conf if needed"
echo "2. Run: sudo python3 evil_twin_portal.py"
echo "3. Connect to MyRepublic_WiFi network"
echo "4. Access portal at: http://192.168.1.1"
echo "5. View logs at: http://192.168.1.1/logs"
echo ""
echo "📚 Read README_EVIL_TWIN.md for detailed instructions"
echo "⚠️  Remember: This is for educational purposes only!" 