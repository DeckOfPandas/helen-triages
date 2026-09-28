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
#
# 24, MATCHING CI (#1203, 2026-09-28). This said 22 while
# .github/workflows/build-and-deploy.yml's setup-node said 24, so the JS suite
# ran on two different majors -- here and in the gate that decides whether the
# site deploys -- for weeks without a difference showing. That is luck, not
# compatibility, and the version a test passed under is part of what the pass
# means. Helen chose to move the container up rather than CI down, since the
# workflow file is hers to edit and this is not.
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Playwright and its headless Chromium, for scripts/browser/ (MANUAL §1), with
# every system library Chromium needs (`--with-deps` apt-installs Playwright's
# own list, which supersedes the hand-picked libs above -- they stay, harmless).
# Helen, 2026-09-15: "shall I pre-install Playwright (and its dependencies) into
# this Docker image?" -- because sessions now start in fresh worktrees, and
# tmp/browser/ belongs to one worktree, so every session that wanted a
# screenshot downloaded a few hundred MB first.
#
# THE VERSION IS PINNED TWICE, HERE AND IN scripts/browser/install.sh, and
# tests/test_browser_harness.py fails if they differ. Bumping it means editing
# both and rebuilding this image. Until the image is rebuilt, install.sh sees
# the old version and installs the pinned one into tmp/browser/ as before.
#
# Root-owned under /opt, readable by the `helen` user without any chmod; the
# harness reads it through scripts/browser/env.sh.
RUN mkdir -p /opt/playwright \
    && cd /opt/playwright \
    && npm init -y > /dev/null \
    && npm install --no-audit --no-fund playwright@1.47.2 \
    && PLAYWRIGHT_BROWSERS_PATH=/opt/playwright/ms-playwright npx playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* /root/.npm

# GitHub CLI, matching the project's own `gh` usage (read/write on Issues
# and PRs via AGENT_GH_TOKEN -- see CLAUDE.md). Said GH_TOKEN until 2026-09-28;
# that credential was retired on 2026-09-09 and DECISIONS §11 keeps its measured
# scope tables only as history.
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
# lives (see README on why). --break-system-packages is safe here: this is a
# disposable, single-purpose container image, not a shared system Python that
# anything else depends on.
#
# THE SYNC IS NOW A TEST, NOT A COMMENT (#1203, 2026-09-28). This used to end
# "keep this in sync with requirements-test.txt by hand if that file's pins
# change", and the pins had already drifted: both files said `>=`, so this image
# carries pytest 9.1.1 under a floor of 8.0 and CI installed whatever was newest
# on the day. Exact pins in requirements-test.txt are the single source, and
# tests/test_devcontainer_pins.py fails if this line disagrees with them. Same
# shape as the Playwright version two blocks up, which is pinned twice with
# tests/test_browser_harness.py holding the two together.
RUN pip install --break-system-packages --no-cache-dir \
    "pytest==9.1.1" "PyYAML==6.0.3" "playwright==1.47.0"

# PLAYWRIGHT'S CHROMIUM FOR THE PYTHON BINDING, which the pip install above does
# NOT fetch -- the package and its browsers are separate downloads (#1200).
#
# Into the SAME PLAYWRIGHT_BROWSERS_PATH the npm install uses, deliberately. PyPI
# has no playwright 1.47.2 (checked 2026-09-28: 1.47.0, then 1.48.0), so the pip
# pin and the npm pin differ by a patch and want different Chromium revisions.
# Sharing the directory lets each find its own rather than making one guess at
# the other's; the cost is at worst a second Chromium in the image, and nothing
# is fragile. Do not try to make the two versions match.
#
# --with-deps is omitted: the npm install above already apt-installed
# Playwright's system library list, and repeating it would only re-fetch apt
# indexes this layer then deletes.
RUN PLAYWRIGHT_BROWSERS_PATH=/opt/playwright/ms-playwright \
    python3 -m playwright install chromium

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
