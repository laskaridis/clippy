FROM mcr.microsoft.com/devcontainers/base:ubuntu

ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VERSION=3.12.13
ARG NODE_VERSION=22.22.2
ARG PNPM_VERSION=9.15.1
ARG CODEX_VERSION=0.128.0
ARG GH_VERSION=2.90.0

ENV REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/bs-certs.crt
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/bs-certs.crt

# Copy and trust the corporate CA cert before networked installs.
COPY bs-certs.pem /usr/local/share/ca-certificates/bs-certs.crt
RUN update-ca-certificates

# Install system dependencies plus toolchain build dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libasound2t64 \
        libatk-bridge2.0-0t64 \
        libatk1.0-0t64 \
        libatspi2.0-0t64 \
        build-essential \
        ca-certificates \
        libcairo2 \
        libcups2t64 \
        curl \
        libdbus-1-3 \
        libgbm1 \
        libglib2.0-0t64 \
        libbz2-dev \
        libffi-dev \
        libgdbm-dev \
        liblzma-dev \
        libncurses5-dev \
        libnss3-dev \
        libpango-1.0-0 \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        postgresql-client \
        tk-dev \
        uuid-dev \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        xz-utils \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Build and install a pinned Python 3.12.x release.
RUN curl -fsSL "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz" -o /tmp/python.tgz \
    && tar -xzf /tmp/python.tgz -C /tmp \
    && cd "/tmp/Python-${PYTHON_VERSION}" \
    && ./configure --with-ensurepip=install \
    && make -j"$(nproc)" \
    && make altinstall \
    && ln -sf /usr/local/bin/python3.12 /usr/local/bin/python3 \
    && ln -sf /usr/local/bin/python3.12 /usr/local/bin/python \
    && ln -sf /usr/local/bin/pip3.12 /usr/local/bin/pip3 \
    && ln -sf /usr/local/bin/pip3.12 /usr/local/bin/pip \
    && rm -rf "/tmp/Python-${PYTHON_VERSION}" /tmp/python.tgz

# Install a pinned Node.js 22.x release directly from the upstream binaries.
RUN arch="$(dpkg --print-architecture)" \
    && case "${arch}" in \
        amd64) node_arch='x64' ;; \
        arm64) node_arch='arm64' ;; \
        *) echo "Unsupported architecture: ${arch}" >&2; exit 1 ;; \
    esac \
    && curl -fsSL "https://nodejs.org/download/release/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" -o /tmp/node.tar.xz \
    && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 --no-same-owner \
    && rm -f /tmp/node.tar.xz

# Enable the pinned pnpm version expected by the extension toolchain.
RUN corepack enable \
    && corepack prepare "pnpm@${PNPM_VERSION}" --activate

# Install a pinned GitHub CLI release.
RUN arch="$(dpkg --print-architecture)" \
    && case "${arch}" in \
        amd64) gh_arch='amd64' ;; \
        arm64) gh_arch='arm64' ;; \
        *) echo "Unsupported architecture: ${arch}" >&2; exit 1 ;; \
    esac \
    && curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${gh_arch}.tar.gz" -o /tmp/gh.tar.gz \
    && tar -xzf /tmp/gh.tar.gz -C /tmp \
    && install "/tmp/gh_${GH_VERSION}_linux_${gh_arch}/bin/gh" /usr/local/bin/gh \
    && rm -rf "/tmp/gh_${GH_VERSION}_linux_${gh_arch}" /tmp/gh.tar.gz

# Install Codex during the image build so repeated container starts hit Docker cache.
RUN npm config set cafile /etc/ssl/certs/ca-certificates.crt \
    && npm install -g "@openai/codex@${CODEX_VERSION}" \
    && npm cache clean --force

# Make plain `pip install ...` work for the vscode user during postCreateCommand.
RUN mkdir -p /home/vscode/.config/pip \
    && printf '[global]\nuser = true\n' > /home/vscode/.config/pip/pip.conf \
    && chown -R vscode:vscode /home/vscode/.config

# Bake the workspace initialization helper into the image so container startup
# can populate the named volume before the devcontainer goes idle.
COPY scripts/init-workspace.sh /usr/local/bin/init-workspace.sh
RUN chmod 0755 /usr/local/bin/init-workspace.sh
