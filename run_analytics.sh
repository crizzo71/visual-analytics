#!/bin/bash

# RedHat LDAP Analytics Dashboard Launcher
echo "🚀 Starting RedHat LDAP Analytics Dashboard..."

# Set environment variables
export PATH="$HOME/.local/bin:$PATH"
export REDHAT_LDAP_CONFIG="$PWD/config/my-ldap.json"
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Check if MCP server is running
if ! curl -s http://127.0.0.1:8814/redhat-ldap-mcp > /dev/null 2>&1; then
    echo "⚠️  MCP server not detected on port 8814"
    echo "💡 Starting MCP server in background..."

    # Start MCP server in background
    nohup uv run python -m redhat_ldap_mcp.server_http --host 127.0.0.1 --port 8814 > mcp_server.log 2>&1 &
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

# Start Streamlit dashboard
echo "🎯 Launching Analytics Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the dashboard"

# Launch Streamlit
uv run streamlit run analytics/dashboard.py --server.port 8501 --server.address 0.0.0.0

echo "🏁 Dashboard stopped"