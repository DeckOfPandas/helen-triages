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
    && npm install --no-audit --no-fund playwright@1.63.0 \
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

# (Claude Code itself is installed at the BOTTOM of this file, not here -- see
# the note there on why it wants to be the last expensive layer.)

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
    "pytest==9.1.1" "PyYAML==6.0.3" "playwright==1.63.0"

# PLAYWRIGHT'S CHROMIUM FOR THE PYTHON BINDING, which the pip install above does
# NOT fetch -- the package and its browsers are separate downloads (#1200).
#
# ONE VERSION IN ALL FOUR PLACES, AND THAT IS THE POINT OF 1.63.0 (2026-09-28).
# The first attempt pinned pip at 1.47.0 to sit beside npm 1.47.2, and PyPI has
# no 1.47.2 at all -- so the two lines could not be made to agree, each wanted
# its own Chromium revision, and the image carried two browsers. Moving both to
# 1.63.0, which exists on npm and PyPI alike, collapses that: the npm pin and the
# pip pin now name one version and resolve to the SAME Chromium revision, so this
# step finds what the npm step already downloaded and there is one browser in the
# image instead of two.
#
# (Deliberately no `name@version` string in this comment: tests/test_browser_harness.py
# counts the npm pins in this file and expects exactly one, which is what makes
# the pin machine-readable. Writing the version in prose broke that test the
# first time -- correctly.)
#
# The number now lives in four files -- here twice, scripts/browser/install.sh,
# and requirements-test.txt -- and two tests hold them together:
# tests/test_browser_harness.py (the npm pins, and now the pip pin against them)
# and tests/test_devcontainer_pins.py (requirements-test.txt against this
# Dockerfile). Bumping it means editing all four and rebuilding the image, which
# is why `playwright` is in dependabot.yml's ignore list: a bot can only ever
# move one of the four.
#
# --with-deps is omitted: the npm install above already apt-installed
# Playwright's system library list, and repeating it would only re-fetch apt
# indexes this layer then deletes.
RUN PLAYWRIGHT_BROWSERS_PATH=/opt/playwright/ms-playwright \
    python3 -m playwright install chromium

# AND WHERE TO FIND IT AT RUN TIME, not only at build time (Helen, 2026-09-29,
# #1200). The two RUN lines above set the path for their own layer and no
# further, so until this line the Python binding, left alone, looked in
# ~/.cache/ms-playwright, found nothing and could not launch. Anything that
# must prefer a worktree's own tmp/browser/ copy still sets the variable itself
# and wins: scripts/browser/env.sh does, and so does tests/test_browser_smoke.py.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright/ms-playwright

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

# CLAUDE CODE, AT WHATEVER VERSION run.sh FOUND ON NPM THIS MORNING (2026-10-04).
# This was a bare `npm install -g` with no version, which reads as "latest" and
# is not: Docker caches a RUN by its text, the text never changed, so the image
# kept the version from the day the layer was first built. And the CLI could not
# repair that itself -- it runs as helen, the global npm folder is root's, and
# every session opened with "auto-update failed: no write permission".
#
# So the version is an ARGUMENT. run.sh asks the registry
# (claude_code_latest.py), passes the number in, and labels the image with it;
# a new release changes this RUN's text and nothing above it.
#
# LAST ON PURPOSE. Everything after a changed layer is rebuilt, and this one
# changes most days. Down here a new release costs one npm install; at its old
# place above the pip and Chromium steps it would have re-run those too.
#
# The default is for a build that passes no argument -- by hand, or VS Code's
# Dev Containers. It works, and it has the old cache problem: `--no-cache`, or
# `--build-arg CLAUDE_CODE_VERSION=<number>`, is how to move it.
ARG CLAUDE_CODE_VERSION=latest
RUN npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}"

# The image is the update mechanism, so the CLI is told not to try: an update
# written inside a `--rm` container would be gone at the next start anyway.
ENV DISABLE_AUTOUPDATER=1

USER helen
WORKDIR /workspace

CMD ["/bin/bash"]
