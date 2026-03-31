FROM ubuntu:24.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH

COPY .tool-versions /tmp/tool-versions

RUN set -eux; \
    python_version="$(awk '$1 == "python" { print $2 }' /tmp/tool-versions)"; \
    node_version="$(awk '$1 == "nodejs" { print $2 }' /tmp/tool-versions)"; \
    pnpm_version="$(awk '$1 == "pnpm" { print $2 }' /tmp/tool-versions)"; \
    printf 'PYTHON_VERSION=%s\nNODE_VERSION=%s\nPNPM_VERSION=%s\n' \
      "$python_version" "$node_version" "$pnpm_version" > /tmp/tool-versions.env

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      bash \
      build-essential \
      ca-certificates \
      curl \
      file \
      gawk \
      git \
      gnupg \
      jq \
      less \
      libasound2t64 \
      libatk-bridge2.0-0 \
      libatk1.0-0 \
      libatspi2.0-0 \
      libcairo2 \
      libdbus-1-3 \
      libdrm2 \
      libegl1 \
      libffi-dev \
      libgbm1 \
      libglib2.0-0 \
      libgtk-3-0 \
      liblzma-dev \
      libnspr4 \
      libnss3 \
      libpango-1.0-0 \
      libpq-dev \
      libreadline-dev \
      libsqlite3-dev \
      libssl-dev \
      libx11-6 \
      libx11-xcb1 \
      libxcb1 \
      libxcomposite1 \
      libxdamage1 \
      libxext6 \
      libxfixes3 \
      libxkbcommon0 \
      libxrandr2 \
      libzstd-dev \
      lsb-release \
      make \
      netcat-openbsd \
      openssh-client \
      openssh-server \
      postgresql \
      postgresql-client \
      procps \
      rsync \
      software-properties-common \
      sudo \
      tk-dev \
      unzip \
      uuid-dev \
      wget \
      xz-utils \
      zip \
      zlib1g-dev; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    install -d -m 0755 /etc/apt/keyrings; \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null; \
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg; \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends gh; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    source /tmp/tool-versions.env; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
      amd64) node_arch='x64' ;; \
      arm64) node_arch='arm64' ;; \
      *) echo "Unsupported architecture: ${TARGETARCH:-unknown}" >&2; exit 1 ;; \
    esac; \
    tmpdir="$(mktemp -d)"; \
    trap 'rm -rf "$tmpdir"' EXIT; \
    curl -fsSLk "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" \
      -o "$tmpdir/node.tar.xz"; \
    tar -xJf "$tmpdir/node.tar.xz" -C /opt; \
    ln -sf "/opt/node-v${NODE_VERSION}-linux-${node_arch}/bin/node" /usr/local/bin/node; \
    ln -sf "/opt/node-v${NODE_VERSION}-linux-${node_arch}/bin/npm" /usr/local/bin/npm; \
    ln -sf "/opt/node-v${NODE_VERSION}-linux-${node_arch}/bin/npx" /usr/local/bin/npx; \
    curl -fsSLk "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz" \
      -o "$tmpdir/python.tgz"; \
    tar -xzf "$tmpdir/python.tgz" -C "$tmpdir"; \
    cd "$tmpdir/Python-${PYTHON_VERSION}"; \
    ./configure --prefix="/opt/python/${PYTHON_VERSION}" --with-ensurepip=install; \
    make -j"$(nproc)"; \
    make install; \
    ln -sf "/opt/python/${PYTHON_VERSION}/bin/python3" /usr/local/bin/python; \
    ln -sf "/opt/python/${PYTHON_VERSION}/bin/python3" /usr/local/bin/python3; \
    ln -sf "/opt/python/${PYTHON_VERSION}/bin/pip3" /usr/local/bin/pip; \
    ln -sf "/opt/python/${PYTHON_VERSION}/bin/pip3" /usr/local/bin/pip3; \
    npm config set strict-ssl false; \
    npm install --global "pnpm@${PNPM_VERSION}" "@openai/codex" "playwright@1.58.2"; \
    ln -sf "/opt/node-v${NODE_VERSION}-linux-${node_arch}/bin/pnpm" /usr/local/bin/pnpm; \
    ln -sf "/opt/node-v${NODE_VERSION}-linux-${node_arch}/bin/codex" /usr/local/bin/codex; \
    ln -sf "/opt/node-v${NODE_VERSION}-linux-${node_arch}/bin/playwright" /usr/local/bin/playwright; \
    export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright; \
    NODE_TLS_REJECT_UNAUTHORIZED=0 playwright install chromium

RUN set -eux; \
    getent group agent >/dev/null || groupadd agent; \
    id -u agent >/dev/null 2>&1 || useradd --gid agent --create-home --shell /bin/bash agent; \
    echo 'agent ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/agent; \
    chmod 0440 /etc/sudoers.d/agent; \
    install -d -m 0755 /var/run/sshd /workspace /exports/extension /var/lib/postgresql/data; \
    chown -R agent:agent /workspace /exports/extension /home/agent; \
    chmod 0700 /var/lib/postgresql/data; \
    sed -ri 's/^#?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config; \
    sed -ri 's/^#?PubkeyAuthentication .*/PubkeyAuthentication yes/' /etc/ssh/sshd_config; \
    sed -ri 's|^#?AuthorizedKeysFile .*|AuthorizedKeysFile .ssh/authorized_keys|' /etc/ssh/sshd_config; \
    printf '\nAllowUsers agent\nPermitUserEnvironment yes\n' >> /etc/ssh/sshd_config

COPY infra/sandbox/entrypoint.sh /usr/local/bin/sandbox-entrypoint

RUN chmod 0755 /usr/local/bin/sandbox-entrypoint

ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    SANDBOX_HOME=/home/agent \
    SANDBOX_WORKSPACE=/workspace/webclippings

WORKDIR /workspace

EXPOSE 22 8000

ENTRYPOINT ["/usr/local/bin/sandbox-entrypoint"]
