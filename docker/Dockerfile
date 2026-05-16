# =============================================================================
# ShikariMCP - Docker Image
# Local-first MCP server for AI-assisted security tooling
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir --prefix=/install .

# ProjectDiscovery and modern Go tools often require a newer Go toolchain than
# Debian stable provides, so build them in a dedicated Go stage.
FROM golang:1.25-bookworm AS gotools

RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@v2.14.0 \
    && go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest \
    && go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@v3.8.0 \
    && go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest \
    && go install -v github.com/projectdiscovery/katana/cmd/katana@latest \
    && go install -v github.com/ffuf/ffuf/v2@latest \
    && go install -v github.com/OJ/gobuster/v3@latest

FROM python:3.12-slim AS runtime

LABEL maintainer="Zaeem20 <duranizaeem@gmail.com>"
LABEL description="ShikariMCP - local-first MCP server for verified security tools"
LABEL version="0.1.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    jq \
    unzip \
    dnsutils \
    net-tools \
    iputils-ping \
    whois \
    nmap \
    masscan \
    netcat-openbsd \
    nikto \
    dirb \
    tcpdump \
    tshark \
    arping \
    john \
    hashcat \
    hydra \
    medusa \
    binwalk \
    sqlmap \
    aircrack-ng \
    sslscan \
    sslyze \
    foremost \
    libimage-exiftool-perl \
    yara \
    socat \
    proxychains4 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin

COPY --from=builder /install /usr/local
COPY --from=gotools /go/bin/subfinder /usr/local/bin/subfinder
COPY --from=gotools /go/bin/httpx /usr/local/bin/httpx
COPY --from=gotools /go/bin/nuclei /usr/local/bin/nuclei
COPY --from=gotools /go/bin/naabu /usr/local/bin/naabu
COPY --from=gotools /go/bin/katana /usr/local/bin/katana
COPY --from=gotools /go/bin/ffuf /usr/local/bin/ffuf
COPY --from=gotools /go/bin/gobuster /usr/local/bin/gobuster

WORKDIR /app
COPY . .

RUN groupadd -r shikari \
    && useradd -r -g shikari -d /home/shikari -s /bin/bash shikari \
    && mkdir -p /home/shikari /app/output /app/.shikari \
    && chown -R shikari:shikari /home/shikari /app

USER shikari

# Docker must listen on all container interfaces for port publishing. HTTP auth
# remains mandatory unless SHIKARI_ALLOW_UNAUTHENTICATED_HTTP is explicitly set.
ENV SHIKARI_TRANSPORT=streamable-http \
    SHIKARI_HOST=0.0.0.0 \
    SHIKARI_PORT=8080 \
    SHIKARI_ENABLE_GENERATED_TOOLS=false \
    SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS=false \
    SHIKARI_AUDIT_ENABLED=true \
    SHIKARI_AUDIT_LOG_PATH=/app/.shikari/audit.jsonl \
    SHIKARI_LOG_LEVEL=INFO

RUN shikari tools verify --profile core --json

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import os,socket; s=socket.create_connection(('127.0.0.1', int(os.getenv('SHIKARI_PORT', '8080'))), 5); s.close()"

ENTRYPOINT ["shikari"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8080"]
