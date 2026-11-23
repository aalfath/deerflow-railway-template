"""DeerFlow Gateway start script for Railway.

1. Renders /app/backend/config.yaml from /app/railway/config.yaml, adding one
   OpenAI-compatible model from LLM_API_KEY / LLM_BASE_URL / LLM_MODEL. The key
   itself stays in the environment ($LLM_API_KEY), never on disk.
2. Waits for Postgres, then runs uvicorn (one worker) on [::]:$PORT.
3. Creates the first admin from ADMIN_EMAIL / ADMIN_PASSWORD through the app's
   own POST /api/v1/auth/initialize on loopback (409 = admin already exists).
   If that fails the service exits 1, so the first-run /setup page never stays
   open on a public URL.
Any unexpected stop exits non-zero, so Railway's ON_FAILURE policy restarts it.
"""
import json, os, re, signal, socket, subprocess, sys, threading, time, urllib.error, urllib.parse, urllib.request

import yaml

PORT = os.environ.get("PORT") or "8001"
HOME = os.environ.get("DEER_FLOW_HOME", "/data")
CFG_IN, CFG_OUT = "/app/railway/config.yaml", os.environ.get("DEER_FLOW_CONFIG_PATH", "/app/backend/config.yaml")


def log(msg):
    print(f"[deerflow-railway] {msg}", flush=True)


def die(msg):
    log("FATAL: " + msg)
    sys.exit(1)


def render_config():
    cfg = yaml.safe_load(open(CFG_IN))
    os.environ.setdefault("LLM_BASE_URL", "")
    os.environ["LLM_BASE_URL"] = os.environ["LLM_BASE_URL"].strip() or "https://api.openai.com/v1"
    os.environ["LLM_MODEL"] = (os.environ.get("LLM_MODEL") or "").strip() or "gpt-5-mini"
    key = (os.environ.get("LLM_API_KEY") or "").strip()
    os.environ["LLM_API_KEY"] = key
    model = os.environ["LLM_MODEL"]
    vision = os.environ.get("LLM_SUPPORTS_VISION", "").strip().lower()
    if vision in ("", "auto"):
        vision_on = urllib.parse.urlparse(os.environ["LLM_BASE_URL"]).hostname == "api.openai.com"
    else:
        vision_on = vision in ("1", "true", "yes", "on")
    if key:
        cfg["models"] = [{
            "name": re.sub(r"[^A-Za-z0-9._-]+", "-", model).strip("-") or "default",
            "display_name": model,
            "use": "langchain_openai:ChatOpenAI",
            "model": "$LLM_MODEL",
            "api_key": "$LLM_API_KEY",
            "base_url": "$LLM_BASE_URL",
            "request_timeout": 600.0,
            "max_retries": 2,
            "supports_vision": vision_on,
        }]
        log(f"model: {model} via {os.environ['LLM_BASE_URL']} (vision={'on' if vision_on else 'off'})")
    else:
        cfg["models"] = []
        log("WARNING: LLM_API_KEY is empty. DeerFlow starts, but chats need a model: set LLM_API_KEY "
            "on the Gateway service, or add a model as admin in Settings.")
    if (os.environ.get("TAVILY_API_KEY") or "").strip():
        for t in cfg.get("tools", []):
            if t.get("name") == "web_search":
                t.clear()
                t.update({"name": "web_search", "group": "web", "use": "deerflow.community.tavily.tools:web_search_tool",
                          "max_results": 5, "api_key": "$TAVILY_API_KEY"})
        log("web_search: Tavily")
    reg = (os.environ.get("ALLOW_REGISTRATION") or "").strip().lower() in ("1", "true", "yes", "on")
    cfg.setdefault("auth", {}).setdefault("local", {})["allow_registration"] = reg
    log("self-registration: " + ("ON (anyone with the URL can create an account)" if reg else "off"))
    os.makedirs(os.path.dirname(CFG_OUT), exist_ok=True)
    with open(CFG_OUT, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)


def prepare_home():
    os.makedirs(HOME, exist_ok=True)
    os.makedirs(os.path.join(HOME, ".cache", "tiktoken"), exist_ok=True)
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", os.path.join(HOME, ".cache", "tiktoken"))
    ext = os.environ.get("DEER_FLOW_EXTENSIONS_CONFIG_PATH", os.path.join(HOME, "extensions_config.json"))
    if not os.path.exists(ext):
        with open(ext, "w") as f:
            json.dump({"mcpServers": {}, "skills": {}}, f)
        log(f"created {ext}")


def wait_for_db(timeout=240):
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        die("DATABASE_URL is not set (it should reference the Postgres service).")
    u = urllib.parse.urlparse(url)
    host, port = u.hostname, u.port or 5432
    end = time.time() + timeout
    while True:
        try:
            socket.create_connection((host, port), timeout=5).close()
            log(f"Postgres reachable at {host}:{port}")
            return
        except OSError as e:
            if time.time() > end:
                die(f"Postgres at {host}:{port} not reachable after {timeout}s: {e}")
            time.sleep(3)


def http(method, path, body=None, timeout=10):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"} if body is not None else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def seed_admin(proc, state):
    email = (os.environ.get("ADMIN_EMAIL") or "").strip()
    password = os.environ.get("ADMIN_PASSWORD") or ""
    end = time.time() + 600
    while proc.poll() is None:
        try:
            if http("GET", "/health", timeout=3)[0] == 200:
                break
        except Exception:
            pass
        if time.time() > end:
            state["seed_failed"] = "gateway did not answer /health within 600s"
            proc.terminate()
            return
        time.sleep(2)
    if proc.poll() is not None:
        return
    try:
        code, body = http("GET", "/api/v1/auth/setup-status")
        if code == 200 and not json.loads(body).get("needs_setup"):
            log("admin account already exists")
            return
        if not email or len(password) < 8:
            raise RuntimeError("no admin exists yet and ADMIN_EMAIL / ADMIN_PASSWORD (8+ chars) are not set")
        code, body = http("POST", "/api/v1/auth/initialize", {"email": email, "password": password, "remember_me": False})
        if code == 201:
            log(f"admin account created: {email} (password: the Gateway's ADMIN_PASSWORD variable)")
        elif code == 409:
            log("admin account already exists")
        else:
            raise RuntimeError(f"/api/v1/auth/initialize answered {code}: {body[:300]}")
    except Exception as e:
        state["seed_failed"] = str(e)
        proc.terminate()


def main():
    render_config()
    prepare_home()
    wait_for_db()
    workers = os.environ.get("GATEWAY_WORKERS") or "1"
    # One dual-stack socket (IPv6 + IPv4): Railway's private network is IPv6, the
    # loopback admin seeding uses IPv4, and asyncio sets IPV6_V6ONLY on "::".
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.bind(("::", int(PORT)))
    sock.set_inheritable(True)
    cmd = [sys.executable, "-m", "uvicorn", "app.gateway.app:app", "--fd", str(sock.fileno()),
           "--workers", workers, "--timeout-graceful-shutdown", "10"]
    env = dict(os.environ, PYTHONPATH="/app/backend")
    log(f"starting Gateway on [::]:{PORT} + 0.0.0.0:{PORT} (workers={workers})")
    proc = subprocess.Popen(cmd, cwd="/app/backend", env=env, pass_fds=(sock.fileno(),))
    sock.close()
    state = {"signal": None, "seed_failed": None}

    def forward(signum, _frame):
        state["signal"] = signum
        if proc.poll() is None:
            proc.send_signal(signum)

    signal.signal(signal.SIGTERM, forward)
    signal.signal(signal.SIGINT, forward)
    threading.Thread(target=seed_admin, args=(proc, state), daemon=True).start()
    rc = proc.wait()
    if state["seed_failed"]:
        die("first-admin setup failed: " + state["seed_failed"])
    if state["signal"] is not None:
        log(f"stopped by signal {state['signal']} (exit {rc})")
        sys.exit(0 if rc in (0, -state["signal"], 128 + state["signal"]) else rc)
    log(f"Gateway exited unexpectedly with code {rc}")
    sys.exit(rc if rc and rc > 0 else 1)


if __name__ == "__main__":
    main()
