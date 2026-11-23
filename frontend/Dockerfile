# DeerFlow web UI (Next.js) for Railway. Official upstream image, pinned by
# release tag and digest. Runs `next start` directly as PID 1 on [::]:$PORT.
FROM ghcr.io/bytedance/deer-flow-frontend:v2.2.0@sha256:a07243038e5de9e8eae49dc36f54a398f26df9e2a5a4beac05f0f0ea666b6dee
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    NODE_OPTIONS=--max-old-space-size=320 \
    UV_THREADPOOL_SIZE=2
WORKDIR /app/frontend
EXPOSE 3000
CMD ["sh", "-c", "exec node node_modules/next/dist/bin/next start -H :: -p \"${PORT:-3000}\""]
