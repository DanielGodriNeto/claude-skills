---
name: repo-howto
description: Use when the user wants to know how EXTERNAL open-source projects do something, or says "find GitHub repos that do X", "has someone built this", or pastes a github.com link and asks how it works or how to replicate it. Finds relevant repos, reads them, and explains the architecture and a plan to replicate it. No need for the user to paste a link or name a tool.
---

# repo-howto

Goal: turn "I want feature X" or a GitHub link into a clear, short how-to.

0. **Token check first:** if the feature is simple or the repo is small, read only the README (and at most 1-2 files) and answer. Use the full digest only for complex repos.
1. **Find repos** (skip if the user gave a link): `gh search repos "<keywords>" --sort stars --limit 8 --json fullName,description,stargazersCount,updatedAt,license`. Also WebSearch if gh finds little. Prefer maintained (pushed in the last 12 months), real stars, permissive license. Pick the best 1-3.
2. **Read each pick**, cheapest first:
   - `gitingest <url> -o -` (read-only digest; if the command is missing, use the `gh` fallback and tell the user, don't pip install). Pipe through `head -c 60000` for big repos.
   - Fallback: `gh repo view <owner/repo>` and `gh api repos/<owner>/<repo>/readme`, then read only the key files.
   - Private repo: use gh, never send a token to a hosted gitingest site.
3. **Answer short**, in the user's language:
   - What it does and how it is structured (3-6 lines, cite files).
   - How to replicate it in the user's stack (steps, libs, pitfalls).
   - License and maintenance caveats; flag anything risky (scraping ToS, secrets, abandoned).
   - If several repos fit, a compact comparison and one recommendation.

Do not clone or install anything from the repo. Read only.
