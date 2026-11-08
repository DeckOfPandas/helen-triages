
# Appended to the container user's ~/.bashrc at build time.
# project.bashrc is read from the bind mount, so editing it needs no rebuild.
# Host dotfiles, when run.sh mounts them, load last. They usually reload
# ~/.bashrc, which in here is THIS file, so the flag stops a second pass;
# without it a shell loops until Ctrl-C. It is not exported, so a child shell
# still loads everything.
if [ -z "$_CONTAINER_RC_DONE" ]; then
  _CONTAINER_RC_DONE=1
  [ -f /workspace/.devcontainer/project.bashrc ] && . /workspace/.devcontainer/project.bashrc
  [ -f "$HOME/.host-bashrc" ] && . "$HOME/.host-bashrc"
  [ -f "$HOME/.host-bash_aliases" ] && . "$HOME/.host-bash_aliases"
  [ -f "$HOME/.host-bash_profile" ] && . "$HOME/.host-bash_profile"
  # The config volume starts empty, so a new project's Claude Code memory gets
  # the kit's notes once; the marker keeps a deleted note deleted.
  [ -f "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/-workspace/memory/.kit-seeded" ] \
    || python3 /workspace/.devcontainer/seed_memory.py
fi
