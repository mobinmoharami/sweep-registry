#!/usr/bin/env bash
# Install the registry app as a systemd service behind nginx.
#   sudo bash app/deploy.sh registry.example.com          # picks a free port
#   sudo bash app/deploy.sh registry.example.com 8477     # forces one
set -euo pipefail
DOMAIN="${1:-}"; WANT="${2:-}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
[ -z "$DOMAIN" ] && { echo "usage: bash app/deploy.sh <domain> [port]"; exit 1; }

command -v python3 >/dev/null || { echo "python3 required"; exit 1; }

# This box runs several projects at once, so never assume a port is free.
pick_port() {
    local p
    for p in $( [ -n "$WANT" ] && echo "$WANT"; seq 8400 8999 ); do
        if ! ss -ltn 2>/dev/null | grep -q ":${p}[[:space:]]"; then
            echo "$p"; return
        fi
    done
    echo "no free port in 8400-8999" >&2; exit 1
}
PORT="$(pick_port)"
[ -n "$WANT" ] && [ "$PORT" != "$WANT" ] && \
    echo "  ! port ${WANT} is in use, using ${PORT}"

[ -d "$DIR/.venv" ] || python3 -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install -q --upgrade pip flask numpy requests

TOKEN_FILE="$DIR/.admin_token"
if [ ! -f "$TOKEN_FILE" ]; then
    head -c 24 /dev/urandom | base64 | tr -d '/+=' > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
fi
TOKEN="$(cat "$TOKEN_FILE")"

cat > /etc/systemd/system/registry.service <<EOF
[Unit]
Description=Strategy Registry
After=network.target

[Service]
Type=simple
WorkingDirectory=${DIR}
Environment=ADMIN_TOKEN=${TOKEN}
Environment=REGISTRY_DB=${DIR}/registry.db
Environment=PORT=${PORT}
ExecStart=${DIR}/.venv/bin/python ${DIR}/app/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

if command -v nginx >/dev/null; then
    cat > /etc/nginx/sites-available/registry <<EOF
server {
    listen 80;
    server_name ${DOMAIN};
    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /static/ {
        alias ${DIR}/app/static/;
        expires 7d;
    }
}
EOF
    ln -sf /etc/nginx/sites-available/registry /etc/nginx/sites-enabled/registry
    nginx -t && systemctl reload nginx
else
    echo "  ! nginx not installed — the app will only be reachable on :${PORT}"
fi

systemctl daemon-reload
systemctl enable --now registry
sleep 2
systemctl --no-pager --lines=5 status registry || true

cat <<EOF

====================================================================
 port ${PORT}   ->   http://${DOMAIN}

 admin queue : http://${DOMAIN}/queue?admin=${TOKEN}
 token saved : ${TOKEN_FILE}   (only copy — keep it)

 logs    : journalctl -u registry -f
 restart : systemctl restart registry
 https   : certbot --nginx -d ${DOMAIN}

 Back up registry.db by copying the file. The records themselves live
 in sweeps/ with their hashes and OpenTimestamps proofs, so losing the
 database loses the queue, not the science.
====================================================================
EOF
