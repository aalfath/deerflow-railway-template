[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template/deerflow-1?utm_medium=integration&utm_source=button&utm_campaign=deerflow)

# DeerFlow on Railway

One-click [Railway](https://railway.com) template for [DeerFlow](https://github.com/bytedance/deer-flow), ByteDance's open-source SuperAgent harness: deep research, writing and coding agents with a chat-style web UI, threads, uploads, skills, memory and MCP tools.

**Version:** DeerFlow **v2.2.0**, from upstream's official images, pinned by digest:

| Service | Folder | Image |
|---|---|---|
| `DeerFlow` (public) | `proxy/` | `nginx:1.31.2-alpine@sha256:54f2a904…` (the nginx build upstream pins) |
| `Gateway` | `gateway/` | `ghcr.io/bytedance/deer-flow-backend:v2.2.0@sha256:5a0c01ae…` |
| `Frontend` | `frontend/` | `ghcr.io/bytedance/deer-flow-frontend:v2.2.0@sha256:a0724303…` |
| `Postgres` | none | Railway's PostgreSQL |

## What you get

- **`DeerFlow`**: nginx on the public domain. It sends `/api/*` to the Gateway and everything else to the web UI, like upstream's `docker/nginx`. The health check is `/healthz`, which answers only when the Gateway answers.
- **`Gateway`**: the FastAPI API and LangGraph agent runtime. `gateway/run.py`:
  - renders `config.yaml` (upstream's v2.2.0 example, with Postgres for threads, checkpoints, users and run events) and adds one OpenAI-compatible model from `LLM_API_KEY`, `LLM_BASE_URL` and `LLM_MODEL`. The key stays in the environment and is never written to disk;
  - waits for Postgres, then runs uvicorn (one worker) on IPv6 and IPv4;
  - creates the first admin from `ADMIN_EMAIL` and `ADMIN_PASSWORD` through DeerFlow's own `/api/v1/auth/initialize`, so the `/setup` page is never open on a public URL;
  - exits non-zero on any unexpected stop, so Railway's `ON_FAILURE` restart policy brings it back.

  The bundled skills come from the same v2.2.0 commit. Uploads, outputs, memory, custom agents and MCP settings live on the volume at `/data`. The health check is `/health/ready` (database and checkpointer).
- **`Frontend`**: the Next.js web UI, private only. It runs `next start` as PID 1.
- **`Postgres`**: Railway's PostgreSQL on its own volume.

## Variables

| Service | Variable | Default | Notes |
|---|---|---|---|
| Gateway | `LLM_API_KEY` | prompt | **Required.** A key for OpenAI or any OpenAI-compatible provider |
| Gateway | `LLM_BASE_URL` | `https://api.openai.com/v1` | The provider's OpenAI-compatible endpoint |
| Gateway | `LLM_MODEL` | `gpt-5-mini` | The model ID at that provider |
| Gateway | `ADMIN_EMAIL` | `admin@example.com` | The first admin's login. Used on first boot only |
| Gateway | `ADMIN_PASSWORD` | generated | The first admin's password. Used on first boot only |
| Gateway | `AUTH_JWT_SECRET`, `DEER_FLOW_INTERNAL_AUTH_TOKEN` | generated | Session and internal secrets |
| Gateway | `ALLOW_REGISTRATION` | `false` | Set it to `true` to let anyone with the URL create an account |
| Gateway | `TAVILY_API_KEY` | empty | Optional. Uses Tavily for web search instead of DuckDuckGo |
| Gateway | `DATABASE_URL`, `GATEWAY_CORS_ORIGINS`, `PORT` | references | Wiring |
| Frontend | `DEER_FLOW_INTERNAL_GATEWAY_BASE_URL`, `DEER_FLOW_TRUSTED_ORIGINS`, `PORT` | references | Wiring |
| DeerFlow | `GATEWAY_UPSTREAM`, `FRONTEND_UPSTREAM`, `PORT` | references | Wiring |

## After deploying

1. Open the `DeerFlow` service's URL and sign in as `admin@example.com`, with the password from the `Gateway` service's `ADMIN_PASSWORD` variable.
2. Change the password in Settings.
3. Start a chat. Admins can add more models in Settings.

## Limits

- **No code execution sandbox.** DeerFlow's sandboxed `bash` needs Docker-in-Docker or Kubernetes, which Railway doesn't offer. The agent's shell tool stays off (upstream's default for its local sandbox). File tools, web search and fetch, skills, memory and MCP servers work.
- **Memory:** every service runs within Railway's 0.5 GB plan limit. The Gateway uses about 300 MB when idle. Long research runs with many sub-agents are better with 1 GB on the Gateway.

## Updates

Railway notifies deployers when this repo's `main` changes. Each DeerFlow update bumps the pinned images and the skills commit, is tested on Railway first, and is described in [CHANGELOG.md](CHANGELOG.md). Read it before you apply an update.

Licence: DeerFlow is MIT-licensed by ByteDance. This wrapper is MIT too.
