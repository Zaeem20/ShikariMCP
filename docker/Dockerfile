# syntax=docker/dockerfile:1.7

FROM python:3.12-slim-bookworm AS python-builder
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir --prefix=/install .

FROM golang:1.25-bookworm AS go-tools
ARG SUBFINDER_VERSION=v2.14.0
ARG HTTPX_VERSION=v1.9.0
ARG NUCLEI_VERSION=v3.8.0
ARG NAABU_VERSION=v2.5.0
ARG KATANA_VERSION=v1.6.1
ARG FFUF_VERSION=v2.1.0
ARG GOBUSTER_VERSION=v3.8.2
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpcap-dev \
    && rm -rf /var/lib/apt/lists/* \
    && go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@${SUBFINDER_VERSION} \
    && go install github.com/projectdiscovery/httpx/cmd/httpx@${HTTPX_VERSION} \
    && go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@${NUCLEI_VERSION} \
    && go install github.com/projectdiscovery/naabu/v2/cmd/naabu@${NAABU_VERSION} \
    && CGO_ENABLED=1 go install github.com/projectdiscovery/katana/cmd/katana@${KATANA_VERSION} \
    && go install github.com/ffuf/ffuf/v2@${FFUF_VERSION} \
    && go install github.com/OJ/gobuster/v3@${GOBUSTER_VERSION}

FROM debian:bookworm-slim AS tool-sources
ARG NIKTO_VERSION=2.6.0
ARG SQLMAP_VERSION=1.9
ARG SECLISTS_VERSION=2024.4
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && git clone --depth 1 --branch ${NIKTO_VERSION} https://github.com/sullo/nikto.git /nikto \
    && git clone --depth 1 --branch ${SQLMAP_VERSION} https://github.com/sqlmapproject/sqlmap.git /sqlmap \
    && git clone --depth 1 --branch ${SECLISTS_VERSION} https://github.com/danielmiessler/SecLists.git /seclists

FROM python:3.12-slim-bookworm AS runtime
LABEL org.opencontainers.image.title="ShikariMCP" \
      org.opencontainers.image.description="Local-first MCP server for verified security tools" \
      org.opencontainers.image.version="0.2.0"

ARG TRIVY_VERSION=v0.71.0
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SHIKARI_TRANSPORT=streamable-http \
    SHIKARI_HOST=0.0.0.0 \
    SHIKARI_PORT=8080 \
    SHIKARI_TOOL_PROFILE=core \
    HOME=/home/shikari \
    XDG_CONFIG_HOME=/app/.shikari/config \
    XDG_CACHE_HOME=/app/.shikari/cache \
    XDG_DATA_HOME=/app/.shikari/data \
    SHIKARI_DEFAULT_WORDLIST=/opt/wordlists/SecLists/Discovery/Web-Content/common.txt \
    SHIKARI_ARTIFACT_DIR=/app/.shikari/artifacts \
    SHIKARI_ENABLE_LEGACY_TOOLS=false \
    SHIKARI_ENABLE_GENERATED_TOOLS=false \
    SHIKARI_ENABLE_EXPERIMENTAL_TOOLS=false \
    SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS=false \
    SHIKARI_AUDIT_ENABLED=true \
    SHIKARI_AUDIT_LOG_PATH=/app/.shikari/audit.jsonl

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        jq \
        libio-socket-ssl-perl \
        libjson-perl \
        libnet-ssleay-perl \
        libpcap0.8 \
        libxml-libxml-perl \
        libxml-writer-perl \
        nmap \
        perl \
        tar \
        whois \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-builder /install /usr/local
COPY --from=go-tools /go/bin/ /usr/local/bin/
COPY --from=tool-sources /nikto/program/ /opt/nikto/
COPY --from=tool-sources /sqlmap/ /opt/sqlmap/
COPY --from=tool-sources /seclists/Discovery/Web-Content/common.txt /opt/wordlists/SecLists/Discovery/Web-Content/common.txt

RUN ln -s /opt/nikto/nikto.pl /usr/local/bin/nikto \
    && ln -s /opt/sqlmap/sqlmap.py /usr/local/bin/sqlmap \
    && curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/9b49920/contrib/install.sh \
        -o /tmp/install-trivy.sh \
    && sh /tmp/install-trivy.sh -b /usr/local/bin ${TRIVY_VERSION} \
    && rm /tmp/install-trivy.sh \
    && groupadd --system shikari \
    && useradd --system --gid shikari --home-dir /home/shikari --create-home shikari \
    && mkdir -p /app/.shikari/artifacts /app/.shikari/config /app/.shikari/cache /app/.shikari/data \
    && chown -R shikari:shikari /app /home/shikari

WORKDIR /app
USER shikari

RUN shikari-mcp tools verify --profile core --json

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', 8080), 3); s.close()"

ENTRYPOINT ["shikari-mcp"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8080"]
