# Changelog

## v2.2.0 (2026-11-23)

First release of this template.

- DeerFlow v2.2.0: `ghcr.io/bytedance/deer-flow-backend:v2.2.0@sha256:5a0c01ae939e4c8b0213b8df4f3fe712ce0663c3fbaf7d83c929274b2e9dfa60` and `ghcr.io/bytedance/deer-flow-frontend:v2.2.0@sha256:a07243038e5de9e8eae49dc36f54a398f26df9e2a5a4beac05f0f0ea666b6dee`. Skills from commit `58fc5bd5` (tag v2.2.0).
- Front proxy: `nginx:1.31.2-alpine@sha256:54f2a904c251d5a34adf545a72d32515a15e08418dae0266e23be2e18c66fefa`.
- Postgres for threads, checkpoints, users and run events. Gateway volume at `/data`.
- First admin created on first boot. Self-registration off by default (`ALLOW_REGISTRATION`).
