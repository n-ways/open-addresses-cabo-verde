# N-Ways Addressing for Cabo Verde: the registry server.
# Build from the repository root (docker compose does this):
#   docker build -f server/Dockerfile -t addresses-cv .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ADDRESSES_DB=/data/addresses.sqlite \
    REGISTRY_DIR=/app/registry \
    PORT=8080

RUN groupadd --system --gid 10001 addresses \
 && useradd --system --uid 10001 --gid addresses --home-dir /app --shell /usr/sbin/nologin addresses \
 && mkdir -p /data && chown addresses:addresses /data

WORKDIR /app
COPY --chown=addresses:addresses engine/reference/cv_engine.py engine/reference/plate_names.py engine/reference/
COPY --chown=addresses:addresses engine/data/ engine/data/
COPY --chown=addresses:addresses registry/ registry/
COPY --chown=addresses:addresses server/ server/
COPY --chown=addresses:addresses LICENSE LICENSE-DATA NOTICE ./

USER addresses
VOLUME ["/data"]
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/v1/health' % os.environ.get('PORT', '8080'), timeout=4)" || exit 1

ENTRYPOINT ["sh", "/app/server/docker-entrypoint.sh"]
