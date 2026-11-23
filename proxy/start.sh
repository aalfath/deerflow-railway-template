#!/bin/sh
# Render the nginx config from Railway variables and run nginx as PID 1.
set -eu
: "${PORT:=8080}"
case "${GATEWAY_UPSTREAM:-}" in ""|":"*) echo "[deerflow-proxy] FATAL: GATEWAY_UPSTREAM is empty" >&2; exit 1 ;; esac
case "${FRONTEND_UPSTREAM:-}" in ""|":"*) echo "[deerflow-proxy] FATAL: FRONTEND_UPSTREAM is empty" >&2; exit 1 ;; esac
# Railway's private DNS resolver is IPv6 (fd12::10); nginx needs it bracketed.
NGINX_RESOLVER="$(awk '/^nameserver/ {print $2}' /etc/resolv.conf | while read -r ns; do case "$ns" in *:*) printf '[%s] ' "$ns";; *) printf '%s ' "$ns";; esac; done | sed 's/ *$//')"
[ -n "$NGINX_RESOLVER" ] || NGINX_RESOLVER="[fd12::10]"
LISTEN_V6="listen [::]:${PORT};"
[ -e /proc/net/if_inet6 ] || LISTEN_V6="# no IPv6 on this host"
export PORT GATEWAY_UPSTREAM FRONTEND_UPSTREAM NGINX_RESOLVER LISTEN_V6
envsubst '${PORT} ${GATEWAY_UPSTREAM} ${FRONTEND_UPSTREAM} ${NGINX_RESOLVER} ${LISTEN_V6}' \
  < /etc/deerflow/nginx.conf.template > /etc/nginx/nginx.conf
echo "[deerflow-proxy] port ${PORT}; gateway ${GATEWAY_UPSTREAM}; frontend ${FRONTEND_UPSTREAM}; resolver ${NGINX_RESOLVER}"
nginx -t -q
exec nginx -g 'daemon off;'
