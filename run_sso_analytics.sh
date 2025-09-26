#!/bin/bash

# RedHat LDAP SSO Analytics Dashboard Launcher
echo "🔐 Starting Red Hat SSO Analytics Dashboard..."

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
    echo "💡 Copy .env.example to .env and configure your Red Hat SSO settings"
fi

# Set default SSO environment variables if not provided
export RH_SSO_BASE_URL="${RH_SSO_BASE_URL:-https://sso.redhat.com}"
export RH_SSO_REALM="${RH_SSO_REALM:-redhat-external}"
export RH_SSO_CLIENT_ID="${RH_SSO_CLIENT_ID:-ldap-analytics-dashboard}"
export RH_SSO_REDIRECT_URI="${RH_SSO_REDIRECT_URI:-http://localhost:8503/callback}"

# Security environment variables
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

echo "🏢 Red Hat SSO Configuration:"
echo "   • SSO Server: $RH_SSO_BASE_URL"
echo "   • Realm: $RH_SSO_REALM"
echo "   • Client ID: $RH_SSO_CLIENT_ID"
echo "   • Redirect URI: $RH_SSO_REDIRECT_URI"
echo "   • Session timeout: $SESSION_TIMEOUT_MINUTES minutes"
echo "   • Audit logging: $ENABLE_AUDIT_LOGGING"

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

# SSO Security checks
echo "🔍 Running SSO security checks..."

# Check for SSO client secret
if [ -z "$RH_SSO_CLIENT_SECRET" ]; then
    echo "⚠️  Warning: RH_SSO_CLIENT_SECRET not set!"
    echo "💡 Set this in your .env file for production use"
fi

# Verify HTTPS requirement for production
if [[ "$RH_SSO_REDIRECT_URI" == http://* ]] && [[ "$RH_SSO_BASE_URL" == https://sso.redhat.com* ]]; then
    echo "⚠️  Warning: Production Red Hat SSO requires HTTPS redirect URI"
    echo "💡 For production, use HTTPS redirect URI"
fi

echo "🛡️  Security recommendations:"
echo "   • Use HTTPS in production environments"
echo "   • Configure reverse proxy (nginx/Apache)"
echo "   • Set up proper firewall rules"
echo "   • Enable VPN access for internal use"
echo "   • Configure rate limiting"
echo "   • Set strong client secrets"

# Start Streamlit SSO dashboard
echo "🎯 Launching Red Hat SSO Analytics Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8503"
echo "🔐 Red Hat SSO authentication required"
echo ""
echo "🏢 SSO Login Flow:"
echo "   1. Click 'Login with Red Hat SSO'"
echo "   2. Authenticate with your Red Hat credentials"
echo "   3. Grant permissions to the application"
echo "   4. You'll be redirected back to the dashboard"
echo ""
echo "🛑 Press Ctrl+C to stop the dashboard"

# Launch Streamlit with SSO dashboard
uv run streamlit run analytics/sso_dashboard.py --server.port 8503 --server.address 127.0.0.1

echo "🏁 SSO dashboard stopped"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    # Kill background processes if they exist
    jobs -p | xargs -r kill
}

# Set trap for cleanup
trap cleanup EXIT