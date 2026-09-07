FROM ruby:3.3-bookworm

# Everything below runs at IMAGE BUILD time, inside Docker's own build
# context -- this is not your host machine, so normal apt-get/npm installs
# here are fine and don't touch anything outside the container.

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    gnupg \
    sudo \
    jq \
    less \
    nano \
    build-essential \
    libyaml-dev \
    libxml2-dev \
    zlib1g-dev \
    iptables \
    ipset \
    iproute2 \
    dnsutils \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Node, for the `claude` CLI itself and the project's JS tests.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# GitHub CLI, matching the project's own `gh` usage (read/write on Issues
# and PRs via GH_TOKEN -- see CLAUDE.md).
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code

# Non-root user matching Helen's host uid/gid (1000), so files the
# container creates on the bind-mounted project directory come back
# owned by her, not root.
RUN groupadd --gid 1000 helen \
    && useradd --uid 1000 --gid 1000 -m -s /bin/bash helen \
    && echo "helen ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/helen-firewall \
    && chmod 0440 /etc/sudoers.d/helen-firewall

COPY init-firewall.sh /usr/local/bin/init-firewall.sh
RUN chmod +x /usr/local/bin/init-firewall.sh

ENV CLAUDE_CONFIG_DIR=/home/helen/.claude
ENV BUNDLE_PATH=/home/helen/.bundle-cache

RUN mkdir -p "$CLAUDE_CONFIG_DIR" "$BUNDLE_PATH" \
    && chown -R helen:helen /home/helen

USER helen
WORKDIR /workspace

CMD ["/bin/bash"]
