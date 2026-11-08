# helen-triages' container

Claude Code runs in a container that sees only this project, bind-mounted at
`/workspace`: no `~/.ssh`, no other projects. The container is the kit's
(helen-contains-claude-webdev): its `Dockerfile`, `run.sh`,
`init-firewall.sh` and the scripts beside them are kit-owned and change only
through `/kit-sync`. What is ours here:

| file | says |
|---|---|
| `kit.env` | Ruby 3.3 and Playwright on, PyYAML from `requirements.txt`, Node 24, and the ports: `jekyll-local`'s 4001 and `jekyll-prod`'s 4002 published on the host as 5998 and 5999 |
| `project.bashrc` | the `jekyll-local` and `jekyll-prod` aliases, sourced by every shell from the bind mount |
| `requirements.txt` | the image's Python packages, pinned |
| `devcontainer.json` | watched, not generated: the kit's template plus VS Code's forwarded ports, `bundle install` on create and the Ruby extension |
| this README | — |

`.dockerignore` (the kit's) leaves this README out of the build stamp, so
editing it never rebuilds the image.

## Run it

From the host, in this checkout or any of its worktrees:

    .devcontainer/run.sh

It builds the image when there is none and rebuilds when `.devcontainer/` or
`kit.env` has changed, reads `AGENT_GH_TOKEN` from
`.claude/settings.local.json` (or your shell), and drops you into
`/workspace` as your own host user. `run.sh --help` lists its flags:
`--rebuild` builds from scratch and pulls the base image again (for an
upstream Ruby or apt change, which nothing on disk shows); `--firewall`
restricts outbound traffic to an allowlist.

The first time on a fresh gem volume, inside the container:

    bundle install

and log Claude Code in once (`claude`, then open the URL it prints in your
host browser; on WSL2 you may be shown a code to paste back). The login lives
in the `helen-triages-claude-config` volume, at `/state/claude-config`, so it
survives every restart.

## VS Code instead

`devcontainer.json` builds through `run.sh --build-only`, so both ways use one
image. Dev Containers: Reopen in Container.

## What moved when this repo took the kit's container

- **The gem cache is a new volume**, `helen-triages-bundle-cache`, so the
  first run needs `bundle install` once. The old
  `helen-triages-bundle-cache-helen-triages` is unused and can be removed with
  `docker volume rm` whenever you like.
- **The Claude Code config volume is the same one**, mounted at
  `/state/claude-config` instead of `/home/helen/.claude`: the login, history
  and memory carry over.
- The image is built on `ruby:3.3-slim-bookworm` rather than the full image.
