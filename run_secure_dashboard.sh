#!/bin/bash

# RedHat LDAP Secure Analytics Dashboard Launcher
echo "🔐 Starting Red Hat Secure Analytics Dashboard..."

# Set environment variables for security
export PATH="$HOME/.local/bin:$PATH"
export REDHAT_LDAP_CONFIG="$PWD/config/my-ldap.json"
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    echo "📋 Loading environment configuration..."
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  No .env file found. Using default configuration."
fi

# Set default security environment variables if not provided
export DASHBOARD_SECRET_KEY="${DASHBOARD_SECRET_KEY:-$(openssl rand -hex 32)}"
export SESSION_TIMEOUT_MINUTES="${SESSION_TIMEOUT_MINUTES:-60}"
export MAX_LOGIN_ATTEMPTS="${MAX_LOGIN_ATTEMPTS:-3}"
export ENABLE_AUDIT_LOGGING="${ENABLE_AUDIT_LOGGING:-true}"

# Create required directories
mkdir -p logs
mkdir -p analytics

# Set secure permissions
chmod 700 logs
chmod 600 config/my-ldap.json 2>/dev/null || true
chmod 600 .env 2>/dev/null || true

echo "🛡️  Security Configuration:"
echo "   • Session timeout: $SESSION_TIMEOUT_MINUTES minutes"
echo "   • Audit logging: $ENABLE_AUDIT_LOGGING"
echo "   • Max login attempts: $MAX_LOGIN_ATTEMPTS"

# Check if MCP server is running
if ! curl -s http://127.0.0.1:8814/redhat-ldap-mcp > /dev/null 2>&1; then
    echo "⚠️  MCP server not detected on port 8814"
    echo "💡 Starting MCP server in background..."

    # Start MCP server in background
    nohup uv run python -m redhat_ldap_mcp.server_http --host 127.0.0.1 --port 8814 > logs/mcp_server.log 2>&1 &
    MCP_PID=$!
    echo "🔧 MCP server started with PID: $MCP_PID"

    # Wait for server to start
    echo "⏳ Waiting for MCP server to start..."
    sleep 5

    # Check if server is running
    if curl -s http://127.0.0.1:8814/redhat-ldap-mcp > /dev/null 2>&1; then
        echo "✅ MCP server is running"
    else
        echo "❌ Failed to start MCP server"
        exit 1
    fi
else
    echo "✅ MCP server already running on port 8814"
fi

echo "🛡️  Security features:"
echo "   • JWT-based session management"
echo "   • Role-based access control"
echo "   • Data masking and filtering"
echo "   • Comprehensive audit logging"
echo "   • Session timeout protection"

echo "🔑 Demo Login Credentials:"
echo "   Admin: crizzo@redhat.com / admin123"
echo "   Viewer: demo@redhat.com / demo123"

# Start Streamlit secure dashboard
echo "🎯 Launching Secure Analytics Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8502"
echo "🔐 Authentication required"
echo ""
echo "🛑 Press Ctrl+C to stop the dashboard"

# Launch Streamlit with secure dashboard
uv run streamlit run analytics/secure_dashboard.py --server.port 8502 --server.address 127.0.0.1

echo "🏁 Secure dashboard stopped"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    # Kill background processes if they exist
    jobs -p | xargs -r kill
}

# Set trap for cleanup
trap cleanup EXIT