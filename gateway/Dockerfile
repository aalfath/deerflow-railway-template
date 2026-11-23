# DeerFlow Gateway (FastAPI API + LangGraph agent runtime) for Railway.
# Official upstream image, pinned by release tag and digest.
FROM ghcr.io/bytedance/deer-flow-backend:v2.2.0@sha256:5a0c01ae939e4c8b0213b8df4f3fe712ce0663c3fbaf7d83c929274b2e9dfa60

# The bundled skills ship in upstream's git repo, not in the image. Fetch them
# from the exact commit the v2.2.0 tag points at, so they match the image.
ARG DEERFLOW_COMMIT=58fc5bd5b8e6ea46538e9481ba06ca2a46e14e2a
RUN python3 -c "import io,tarfile,urllib.request,sys; \
c='${DEERFLOW_COMMIT}'; \
d=urllib.request.urlopen('https://codeload.github.com/bytedance/deer-flow/tar.gz/'+c, timeout=120).read(); \
t=tarfile.open(fileobj=io.BytesIO(d)); p='deer-flow-'+c+'/skills/'; \
m=[x for x in t.getmembers() if x.name.startswith(p)]; \
[setattr(x,'name','skills/'+x.name[len(p):]) for x in m]; \
t.extractall('/app', members=m, filter='data'); print(len(m),'skill files')" \
 && test -d /app/skills/public/deep-research

COPY config.yaml /app/railway/config.yaml
COPY run.py /app/railway/run.py

ENV DEER_FLOW_PROJECT_ROOT=/app \
    DEER_FLOW_HOME=/data \
    DEER_FLOW_CONFIG_PATH=/app/backend/config.yaml \
    DEER_FLOW_EXTENSIONS_CONFIG_PATH=/data/extensions_config.json \
    DEER_FLOW_SKILLS_PATH=/app/skills \
    DEER_FLOW_ENV=production \
    GATEWAY_ENABLE_DOCS=false \
    DEER_FLOW_FILE_IO_WORKERS=2 \
    DEER_FLOW_ASSEMBLY_WORKERS=2 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    CI=true \
    AUTH_TRUSTED_PROXIES=fd12::/16,10.0.0.0/8,100.64.0.0/10 \
    PORT=8001

WORKDIR /app/backend
EXPOSE 8001
CMD ["/app/backend/.venv/bin/python", "/app/railway/run.py"]
