#!/bin/sh
# Entrypoint script to configure nginx with backend URL from environment
set -eu

# Default to sonotheia-backend.onrender.com if BACKEND_URL is not set
BACKEND_URL="${BACKEND_URL:-https://sonotheia-backend.onrender.com}"

# Determine which nginx conf to edit
CONF_DEFAULT="/etc/nginx/conf.d/default.conf"
CONF_NGINX="/etc/nginx/conf.d/nginx.conf"
if [ -f "$CONF_DEFAULT" ]; then
  TARGET_CONF="$CONF_DEFAULT"
elif [ -f "$CONF_NGINX" ]; then
  TARGET_CONF="$CONF_NGINX"
else
  echo "Error: No nginx conf found in /etc/nginx/conf.d/"
  ls -la /etc/nginx/conf.d/ 2>/dev/null || echo "Directory listing failed"
  exit 1
fi

echo "Configuring nginx to proxy API to: ${BACKEND_URL}"
# Replace the default backend URL placeholder in the selected config file
sed -i "s|https://sonotheia-backend.onrender.com|${BACKEND_URL}|g" "$TARGET_CONF"

# Extract hostname from BACKEND_URL (strip protocol and path, case-insensitive)
BACKEND_HOST=$(echo "$BACKEND_URL" | sed -e 's|^[a-zA-Z]*://||' -e 's|/.*$||' -e 's|:.*$||')

# Maximum wait time for DNS resolution (in seconds)
MAX_WAIT=${DNS_WAIT_TIMEOUT:-60}
WAIT_INTERVAL=2
WAITED=0

# Wait for backend DNS to be resolvable with timeout
echo "Waiting for backend DNS resolution: $BACKEND_HOST (timeout: ${MAX_WAIT}s)"
if command -v getent >/dev/null 2>&1; then
    while ! getent hosts "$BACKEND_HOST" >/dev/null 2>&1; do
        if [ "$WAITED" -ge "$MAX_WAIT" ]; then
            echo "Warning: DNS resolution timeout for $BACKEND_HOST after ${MAX_WAIT}s; continuing anyway"
            break
        fi
        echo "Waiting for $BACKEND_HOST to be resolvable... (${WAITED}s/${MAX_WAIT}s)"
        sleep $WAIT_INTERVAL
        WAITED=$((WAITED + WAIT_INTERVAL))
    done
    if [ "$WAITED" -lt "$MAX_WAIT" ]; then
        echo "Backend $BACKEND_HOST is resolvable"
    fi
elif command -v ping >/dev/null 2>&1; then
    while ! ping -c 1 -W 2 "$BACKEND_HOST" >/dev/null 2>&1; do
        if [ "$WAITED" -ge "$MAX_WAIT" ]; then
            echo "Warning: DNS resolution timeout for $BACKEND_HOST after ${MAX_WAIT}s; continuing anyway"
            break
        fi
        echo "Waiting for $BACKEND_HOST to be resolvable... (${WAITED}s/${MAX_WAIT}s)"
        sleep $WAIT_INTERVAL
        WAITED=$((WAITED + WAIT_INTERVAL))
    done
    if [ "$WAITED" -lt "$MAX_WAIT" ]; then
        echo "Backend $BACKEND_HOST is resolvable"
    fi
else
    echo "Warning: Neither getent nor ping available; skipping DNS wait"
fi

# Start nginx in foreground
exec nginx -g 'daemon off;'
