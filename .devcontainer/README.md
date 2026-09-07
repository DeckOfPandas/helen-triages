# Running Claude Code for this project inside Docker

This gives Claude Code a container that can only see this project directory
(bind-mounted at `/workspace`) — nothing else from your machine. No `~/.ssh`,
no `~/.bashrc`, no other projects. It cannot escape that boundary through
`cat`/`grep`/any Bash command, because those files simply do not exist
inside the container's filesystem, mounted or otherwise.

This is not third-party guesswork -- the base approach (Dockerfile +
optional egress firewall) mirrors Anthropic's own reference setup at
https://github.com/anthropics/claude-code/tree/main/.devcontainer and
https://code.claude.com/docs/en/devcontainer.md, adapted for this project's
actual toolchain (Ruby/Jekyll + Node + Python + `gh`), and everything below
has been built and run end-to-end, not just written.

There are two ways to use it: plain `docker` on the command line (no VS
Code needed -- this matches how you already use Claude Code), or VS Code's
Dev Containers extension, which automates the mounting/rebuild bookkeeping
for you. Pick one; both use the same `Dockerfile`.

## Phase 1: basic sandboxed container (do this first)

### 1. Prerequisite

Docker is already installed and working on this machine (`docker version`
succeeds). If you're setting this up somewhere else, you'd want Docker
Desktop with the WSL2 backend on Windows/WSL2, or a normal Docker Engine
install on native Linux/macOS.

### 2. Build the image

From the repo root:

    docker build -t helen-triages-devcontainer -f .devcontainer/Dockerfile .devcontainer

(The build context is `.devcontainer/` itself, not the whole repo -- the
Dockerfile only needs `init-firewall.sh` from that folder. Your project
files are never copied into the image; they're bind-mounted at runtime,
so editing them doesn't require rebuilding.)

### 3. Create the two named volumes (one-time)

These persist your Claude Code login and your gem cache across container
restarts and rebuilds, so you don't reauthenticate or re-`bundle install`
every time:

    docker volume create helen-triages-claude-config
    docker volume create helen-triages-bundle-cache

### 4. Run it

    docker run -it --rm \
      -v "$(pwd):/workspace" \
      -v helen-triages-claude-config:/home/helen/.claude \
      -v helen-triages-bundle-cache:/home/helen/.bundle-cache \
      -w /workspace \
      helen-triages-devcontainer \
      bash

You're now in a shell inside the container, at `/workspace`, as user
`helen` (not root), looking at this actual project directory.

Tip: save that as a one-line script (e.g. `.devcontainer/run.sh`) once
you've confirmed it works the way you want, so you don't retype it.

### 5. First-time Claude Code login (Max plan, no API key needed)

Inside the container:

    bundle install     # first time only, or after Gemfile.lock changes
    claude

Claude Code will print a login URL (or offer to copy it). Since the
container has no browser of its own:

- Open that URL in your **normal browser on your host machine** and sign
  in with your Claude.ai account (the same Max subscription you already
  use -- no API key, no extra billing).
- After you approve, one of two things happens:
  - It completes automatically and the terminal shows `Login successful`.
  - The browser instead shows you a short code. If so, paste that code
    back at the container's terminal prompt when it asks.
- That second path (manual code paste) is common specifically on
  WSL2 -- it's expected, not a sign anything's broken.

Because `~/.claude` is a named volume (not baked into the image), this
login persists. Next time you `docker run` the same volume, you're
already signed in.

### 6. Use it

From here it's normal Claude Code, just running inside the container:
edit files, run `bundle exec jekyll build`, run the JS tests
(`node --test tests/js/*.test.js`), use `gh`/`git` as usual (your
`GH_TOKEN` still needs to be passed in -- add `-e GH_TOKEN` to the
`docker run` command, sourced from your host shell, so it's never baked
into the image or written to disk in the container).

Exit the container (`exit` or Ctrl+D) whenever -- `--rm` cleans up the
container itself, but the two named volumes (login, gem cache) survive
for next time.

## Phase 2 (optional): egress firewall

Phase 1 already stops Claude reading anything outside `/workspace` --
that's a filesystem guarantee, not a network one. Phase 2 adds a second,
independent layer: even outbound network requests get restricted to a
specific allowlist (Anthropic's API/claude.ai, GitHub, npm, RubyGems),
so a mistaken or malicious command can't phone home to an arbitrary
host either.

This needs two extra Linux capabilities on the container
(`NET_ADMIN`, `NET_RAW`) to let it install `iptables` rules for itself.
Run it once per container start, as root via `sudo` (the container user
has passwordless sudo for exactly this one script, nothing else):

    docker run -it --rm --cap-add=NET_ADMIN --cap-add=NET_RAW \
      -v "$(pwd):/workspace" \
      -v helen-triages-claude-config:/home/helen/.claude \
      -v helen-triages-bundle-cache:/home/helen/.bundle-cache \
      -w /workspace \
      helen-triages-devcontainer \
      bash -c "sudo /usr/local/bin/init-firewall.sh && exec bash"

It prints what it resolved and allowed, then self-tests
(`example.com` should fail, `api.github.com` should succeed) so you can
see immediately if something's misconfigured rather than finding out
later when a legitimate request mysteriously fails.

If a legitimate host gets blocked (say a gem or npm dependency fetches
from a CDN not on the list), add it to the `ALLOWED_DOMAINS` array at the
top of `init-firewall.sh` and re-run.

## Using VS Code's Dev Containers instead

If you'd rather VS Code handle the mounting/volumes for you:
`.devcontainer/devcontainer.json` is already set up to match Phase 1
above (same volumes, same env). Install the "Dev Containers" extension,
open this repo in VS Code, then Command Palette →
**Dev Containers: Reopen in Container**. First-time login works the same
way as step 5 above. The firewall (Phase 2) isn't wired into
`devcontainer.json` by default -- add
`"runArgs": ["--cap-add", "NET_ADMIN", "--cap-add", "NET_RAW"]` and a
`postStartCommand` running the script if you want it there too.

## What this does and doesn't protect against

Does: stops Claude Code (or a mistaken command it runs) from ever seeing
or reading `~/.ssh`, `~/.bashrc`, other projects, or anything else on
your host outside this repo -- structurally, not by convention or
allow-list discipline.

Doesn't: this is not a defense against a genuinely malicious,
sophisticated attack that already has code execution and specifically
knows to look for ways out of a container (Anthropic's own docs carry
the same caveat for their reference setup). The actual threat model this
is built for is the same one that prompted it -- an honest mistake by
Claude, not a targeted attack.
