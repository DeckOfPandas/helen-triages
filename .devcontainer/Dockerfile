# Claude Code sandbox image. Build it through .devcontainer/run.sh, which reads
# kit.env and passes each toggle in as a build argument. The defaults here are
# for a bare `docker build` and match kit.env's shipped values.
#
# Every ARG sits immediately above the block that uses it: Docker hands a
# declared ARG to every later RUN, so one declared at the top would make any
# toggle rebuild the whole image. Blocks are ordered by how often they change.

# run.sh sets this to ruby:<version>-slim-bookworm when WITH_RUBY=1. Both are
# Debian bookworm, so every block below works on either.
ARG BASE_IMAGE=debian:bookworm-slim
FROM ${BASE_IMAGE}

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    gnupg \
    sudo \
    jq \
    less \
    nano \
    procps \
    iptables \
    ipset \
    iproute2 \
    dnsutils \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

ARG NODE_MAJOR=24
RUN curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Always present: scripts/gh-*.sh need it.
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# Ruby itself comes from the base image; this adds what native gems compile
# against. It fails loudly if the base has no Ruby, which means a hand build
# set WITH_RUBY=1 without the matching BASE_IMAGE.
ARG WITH_RUBY=0
RUN if [ "$WITH_RUBY" = 1 ]; then \
      command -v ruby >/dev/null \
        || { echo "WITH_RUBY=1 but the base image has no ruby: build through run.sh" >&2; exit 1; }; \
      apt-get update \
      && apt-get install -y --no-install-recommends build-essential libyaml-dev libxml2-dev zlib1g-dev \
      && rm -rf /var/lib/apt/lists/*; \
    fi
ENV BUNDLE_PATH=/state/bundle

# The npm and pip bindings are pinned to ONE version so they resolve to one
# revision of each browser; two versions would put two of each in the image.
# WebKit is the engine nearest Safari.
ARG WITH_PLAYWRIGHT=0
ARG PLAYWRIGHT_VERSION=1.63.0
RUN if [ "$WITH_PLAYWRIGHT" = 1 ]; then \
      mkdir -p /opt/playwright && cd /opt/playwright \
      && npm init -y > /dev/null \
      && npm install --no-audit --no-fund "playwright@${PLAYWRIGHT_VERSION}" \
      && PLAYWRIGHT_BROWSERS_PATH=/opt/playwright/ms-playwright npx playwright install --with-deps chromium webkit \
      && pip install --break-system-packages --no-cache-dir "playwright==${PLAYWRIGHT_VERSION}" \
      && rm -rf /var/lib/apt/lists/* /root/.npm; \
    fi
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright/ms-playwright
ENV NODE_PATH=/opt/playwright/node_modules

# --break-system-packages is safe in a single-purpose image: nothing else
# depends on this Python. pytest is always here because tests/kit/ ships in
# every project made from the kit.
RUN pip install --break-system-packages --no-cache-dir "pytest==9.1.1"

ARG WITH_PY_REQS=0
COPY requirements.txt /usr/local/share/claude-kit/requirements.txt
RUN if [ "$WITH_PY_REQS" = 1 ]; then \
      pip install --break-system-packages --no-cache-dir -r /usr/local/share/claude-kit/requirements.txt; \
    fi

# The host user's own name, uid and gid, so files written to the bind mount
# come back owned by them. A base-image user already holding the uid or the
# name is removed; an existing group with the gid is reused.
ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000
RUN set -eu; \
    for existing in "$(getent passwd "$USER_UID" | cut -d: -f1)" "$(getent passwd "$USERNAME" | cut -d: -f1)"; do \
      [ -n "$existing" ] && userdel -r "$existing" 2>/dev/null || true; \
    done; \
    getent group "$USER_GID" >/dev/null || groupadd --gid "$USER_GID" "$USERNAME"; \
    useradd --uid "$USER_UID" --gid "$USER_GID" -m -s /bin/bash "$USERNAME"; \
    echo "$USERNAME ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/claude-kit-firewall; \
    chmod 0440 /etc/sudoers.d/claude-kit-firewall; \
    mkdir -p /state/claude-config /state/bundle; \
    chown -R "$USER_UID:$USER_GID" /state

# Named volumes mount over these two, and a new volume takes the ownership the
# image gives the path, so the chown above is what lets the user write there.
ENV CLAUDE_CONFIG_DIR=/state/claude-config

# The allowlist is fixed at build time in a root-owned file, so nothing inside
# the container can widen it. init-firewall.sh adds its own built-in hosts.
COPY init-firewall.sh /usr/local/bin/init-firewall.sh
ARG EXTRA_ALLOWED_DOMAINS=""
RUN chmod 0755 /usr/local/bin/init-firewall.sh \
    && mkdir -p /etc/claude-kit \
    && { \
      if [ "$WITH_RUBY" = 1 ]; then printf '%s\n' rubygems.org index.rubygems.org; fi; \
      if [ "$WITH_PY_REQS" = 1 ]; then printf '%s\n' pypi.org files.pythonhosted.org; fi; \
      for domain in $EXTRA_ALLOWED_DOMAINS; do printf '%s\n' "$domain"; done; \
    } > /etc/claude-kit/allowed-domains

# Managed settings apply to every Claude session in the container, wherever it
# starts, and root owns them, so nothing inside can switch the hook off. It
# warns a session started in a nested clone, where the project's hooks don't run.
COPY managed-settings.json /etc/claude-code/managed-settings.json
COPY session-place.py /usr/local/share/claude-kit/session-place.py

# container.bashrc guards against host dotfiles that reload ~/.bashrc.
COPY container.bashrc /usr/local/share/claude-kit/container.bashrc
RUN cat /usr/local/share/claude-kit/container.bashrc >> "/home/$USERNAME/.bashrc" \
    && chown "$USER_UID:$USER_GID" "/home/$USERNAME/.bashrc"

# LAST, because it changes most often. run.sh passes the version npm calls
# latest; a literal `latest` here would be a cache hit forever. The CLI cannot
# update itself (the npm prefix is root's and the container is --rm), so the
# image is the update mechanism.
ARG CLAUDE_CODE_VERSION=latest
RUN npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}"
ENV DISABLE_AUTOUPDATER=1

USER ${USERNAME}
WORKDIR /workspace
CMD ["/bin/bash"]
