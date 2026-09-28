# #1195: test a pull request before it can be merged

Two changes. **Both are yours** — the agent account's token is classic `repo`
scope without `workflow`, so it cannot push anything under `.github/workflows/`
at all, and repository settings were never ours. This file is the exact text to
paste, so the part that needs a person is only the pasting.

## 1. The trigger — `.github/workflows/build-and-deploy.yml`

Replace the `on:` block at the top. It currently reads:

```yaml
on:
  push:
    branches: ["main"]
  workflow_dispatch:
```

with:

```yaml
on:
  push:
    branches: ["main"]
  # TEST A PULL REQUEST BEFORE IT CAN BE MERGED. GitHub issue #1195.
  #
  # Until 2026-09-28 this workflow ran only AFTER a merge, so the suite that
  # gates the deploy had no chance to speak before `main` moved. That is the
  # entire mechanism behind the three-day silent deploy outage in September
  # (DECISIONS §12, MANUAL §10): one red merge stopped every LATER merge
  # shipping, and the only signal was an Actions email nobody reads. About
  # twenty merges shipped nothing.
  #
  # Every rule written since -- `scripts/main-ci-status.sh`, "report a red main
  # first, before the work you came for", "never merge over a known-red suite"
  # -- DETECTS that outage. None of them PREVENTS it. This does: with the `test`
  # job also required as a status check (step 2), a red merge becomes
  # impossible rather than merely reportable.
  #
  # Only `test` runs here. `build` and `deploy` stay on `push: main`, because
  # they publish -- see the `if` on each below. Drafts are excluded from CI by
  # ruling (#540), so this needs no secret and runs the same ~10,660 tests a
  # push does. Cost: one runner per PR push, a few minutes.
  pull_request:
    branches: ["main"]
  workflow_dispatch:
```

Then add an `if` to the two publishing jobs, so a pull request runs `test` and
stops there. **This part is not in #1195 and it matters** — without it, every PR
would try to deploy to GitHub Pages:

```yaml
  build:
    needs: test
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest
```

```yaml
  deploy:
    if: github.event_name != 'pull_request'
    environment:
      name: github-pages
```

The `concurrency: group: "pages"` block can stay as it is. It serialises
everything, so two PRs will queue rather than run in parallel; if that gets
irritating, change it to:

```yaml
concurrency:
  group: pages-${{ github.ref }}
  cancel-in-progress: false
```

which keeps deploys serialised per branch and lets PR test runs proceed
independently.

## 2. The required status check — repository settings

GitHub → the repo → **Settings** → **Branches** → **Add branch protection
rule** (or edit the existing rule for `main`):

- Branch name pattern: `main`
- Tick **Require status checks to pass before merging**
- Search for and select **`test`** — it will only appear in that list *after*
  the workflow above has run at least once on a pull request, so merge the
  trigger change first, open any PR, let it run, then come back here.
- Leave **Require a pull request before merging** to taste. You already work
  this way by habit; ticking it makes the habit structural.

The 2026-09-15 session offered three options for making CI visible — a README
badge, a workflow line, and a required status check — and recorded that the
check "is a repository setting and hers" (DECISIONS §13, #1093). The
`pull_request` trigger was not among the three, which is why this is still open.

## The suite will still pass after you paste this — checked, not assumed

`tests/test_site_config.py` reads this workflow in two tests, so it is the thing
most likely to object. It asserts:

- a `test` job exists;
- `build` declares `needs: test`;
- `fetch-depth: 0` on the checkout;
- the JS suite is invoked with a glob;
- the build runs `bundle exec jekyll build` and never passes `--safe`.

**None of them constrains the `on:` block**, and adding an `if:` to `build` does
not remove its `needs: test`. So nothing above goes red. Verified against
`test_the_deploy_workflow_runs_the_tests_and_gates_on_them` and
`test_the_deploy_workflow_does_not_use_a_pages_native_build` on 2026-09-28.

Worth knowing rather than discovering: after this lands, a PR's `test` run is the
first thing that has ever tested a branch before merge, so **the first few PRs
may well go red on things that were already broken on `main`** and simply never
had a chance to speak. That is the mechanism working, not a new regression.

## What I could verify, and what I could not

- `origin/main`'s workflow triggers on `push: main` and `workflow_dispatch`
  only — checked 2026-09-28, so the first box on #1195 does not describe the
  tree.
- `GET /repos/DeckOfPandas/helen-triages/branches/main/protection` returns
  **404**. That is consistent with "no protection rule exists", but reading
  protection needs admin rights, so it is *also* consistent with the agent
  account simply not being allowed to see one. **I cannot tell these apart**, so
  if you have already added the check, step 2 is done and only step 1 remains.
