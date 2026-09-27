FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ATLAS_WEBHOOK_HOST=0.0.0.0 \
    ATLAS_WEBHOOK_PORT=8787

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements.txt

COPY atlas ./atlas

RUN useradd --create-home --uid 10001 atlas \
    && mkdir -p /app/work \
    && chown -R atlas:atlas /app

USER atlas

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; port=os.environ.get('PORT') or os.environ.get('ATLAS_WEBHOOK_PORT','8787'); urllib.request.urlopen('http://127.0.0.1:'+port+'/health',timeout=3).read()"

CMD ["python", "-m", "atlas.webhook"]
