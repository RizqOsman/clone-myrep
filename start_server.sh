#!/bin/bash

echo "🚀 Starting MyRepublic Broadband Promo Server..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if server.py exists
if [ ! -f "server.py" ]; then
    echo "❌ server.py not found. Please make sure you're in the correct directory."
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

echo "✅ Python 3 found"
echo "✅ Server file found"
echo "✅ Data directory ready"
echo ""
echo "🌐 Starting server on http://localhost:8000"
echo "📁 Data will be saved to:"
echo "   - data/users.json (user registrations)"
echo "   - data/login_logs.json (login logs)"
echo ""
echo "🔗 Available pages:"
echo "   - Main: http://localhost:8000"
echo "   - Login: http://localhost:8000/login.html"
echo "   - Register: http://localhost:8000/register.html"
echo "   - Admin: http://localhost:8000/admin"
echo ""
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 server.py 