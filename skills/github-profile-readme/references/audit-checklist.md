# Audit checklist

## Which repos to pin (4 to 6)

| Criterion | Pin if |
|---|---|
| Measurable | It shows something checked or measured (benchmark, tests, a live demo), not only "I followed a tutorial" |
| README | Has problem, motivation, stack, image, how to run |
| Visual | Has a screenshot, GIF or hosted demo |
| Fresh enough | Touched in the last year, or clearly finished |
| Original | Not a fork with no changes, not a course exercise |

Everything else: merge loose exercises into one `studies`/`exercises` repo and **archive** the rest (Settings > Archive). Never delete.

## Per-repo checklist

- README exists and opens with what it does in one line.
- Screenshot or demo link near the top; run instructions that work.
- License if it is meant to be reused.
- No secrets, `.env`, personal paths, large binaries in history.
- Description and topics set on the repo page.

## Read-only listing

```bash
gh repo list <user> --limit 200 --json name,isPrivate,isFork,isArchived,diskUsage,pushedAt,description \
  --jq '.[] | [.name, .isPrivate, .isFork, .isArchived, .diskUsage, .pushedAt[:10]] | @tsv'
# README presence per repo (404 = missing)
gh api repos/<user>/<repo>/readme --silent && echo ok || echo missing
# secret and environment NAMES only (never values)
gh api repos/<user>/<user>/actions/secrets --jq '.secrets[].name'
gh api repos/<user>/<user>/environments --jq '.environments[].name'
```

## Abnormally heavy repo (read-only)

```bash
git clone --mirror <url> tmp.git && cd tmp.git
git count-objects -vH
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob"' | sort -k3 -n -r | head -20
```

Report the biggest blobs and which commit added them. Rewriting history is the user's decision, never automatic.

## Honest advice for recruiters

Few strong repos, a README with the problem and how to run it, one visual per project. Streaks and the green graph prove little; do not game them.
