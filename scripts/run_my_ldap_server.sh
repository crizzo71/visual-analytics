#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"
export REDHAT_LDAP_CONFIG="$PWD/config/my-ldap.json"
exec uv run python -m redhat_ldap_mcp.server "$@"