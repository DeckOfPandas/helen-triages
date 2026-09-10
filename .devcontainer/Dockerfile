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
    vim \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    fonts-liberation\
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

# Python test dependencies (tests/test_front_matter.py etc., run via pytest).
# Hardcoded rather than COPYing requirements-test.txt, since the build
# context here is .devcontainer/ itself, not the repo root where that file
# lives (see README on why) -- keep this in sync with requirements-test.txt
# by hand if that file's pins change. --break-system-packages is safe here:
# this is a disposable, single-purpose container image, not a shared system
# Python that anything else depends on.
RUN pip install --break-system-packages --no-cache-dir "pytest>=8.0" "PyYAML>=6.0"

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

# Container-local equivalents of the jekyll-local/jekyll-prod aliases from
# Helen's host ~/.bashrc (not visible in here -- see .devcontainer/README.md
# on why that's deliberate). --host 0.0.0.0 is the part that differs from
# the host versions: Jekyll's default 127.0.0.1-only bind is invisible from
# outside the container even with the port published, so these need to
# listen on every interface to be reachable at all.
RUN echo '' >> /home/helen/.bashrc \
    && echo "alias jekyll-local='bundle exec jekyll serve --config _config.yml,_config_local.yml --port 4001 --host 0.0.0.0'" >> /home/helen/.bashrc \
    && echo "alias jekyll-prod='JEKYLL_ENV=production bundle exec jekyll serve --config _config.yml --port 4002 --host 0.0.0.0'" >> /home/helen/.bashrc \
    && echo '' >> /home/helen/.bashrc \
    && echo '# Optional: run.sh bind-mounts Helen'"'"'s real dotfiles here (read-only,' >> /home/helen/.bashrc \
    && echo '# only if she opted in) at alternate paths so they layer on top of the' >> /home/helen/.bashrc \
    && echo '# aliases above instead of overwriting this file outright.' >> /home/helen/.bashrc \
    && echo '[ -f "$HOME/.host-bashrc" ] && . "$HOME/.host-bashrc"' >> /home/helen/.bashrc \
    && echo '[ -f "$HOME/.host-bash_aliases" ] && . "$HOME/.host-bash_aliases"' >> /home/helen/.bashrc \
    && echo '[ -f "$HOME/.host-bash_profile" ] && . "$HOME/.host-bash_profile"' >> /home/helen/.bashrc \
    && chown helen:helen /home/helen/.bashrc

USER helen
WORKDIR /workspace

CMD ["/bin/bash"]
