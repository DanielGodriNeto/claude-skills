# claude-skills

A small, opinionated Claude Code setup focused on two things: **spending fewer tokens** and **getting better results per task**. It is the configuration I actually use, with personal paths removed so you can adapt it.

The core idea: do not run the same heavy process on every task. A single writer plus an executable check is the default; the full plan, critique and review cycle is kept for risky work.

## What is inside

| Folder | Content |
|---|---|
| `skills/` | Four skills I wrote (table below) |
| `agents/` | Six subagents with fixed model and effort: `explorer`, `researcher`, `implementer`, `planner`, `critic`, `reviewer`. They answer in a short fixed template to save tokens |
| `hooks/` | `build-prompt-nudge.mjs` (route reminder on build/improve prompts), `compact-nudge.mjs` (suggests `/compact` after many tool calls), `plugin-hook.mjs` (turns on-demand plugins on when you ask), `skill-install-gate.ps1` (blocks installing skills or plugins until they were scanned) |
| `scripts/` | `context-audit.mjs` (estimates the always-loaded token cost), `config-audit.mjs` (offline audit of your `.claude` folder, 0 tokens, caches a clean result), `plugin-toggle.mjs`, `sync-readme.mjs` (maintenance script for this repo) |
| `examples/` | `CLAUDE.global.example.md` (routes R0-R4, risk list, git policy) and `settings.example.json` |

<!-- SKILLS_TABLE_START -->
| Skill | Purpose |
|---|---|
| `big-task-workflow` | Routes R0-R4: effort scaled by task type and risk, from a direct fix to a full plan/critic/review cycle |
| `feature-assessment` | Honest feasibility and risk verdict with percentages before building something non-trivial |
| `repo-howto` | Find and evaluate GitHub repositories that solve a problem, with a token check first |
| `project-map` | Turn a project into a navigable map (graphify and an Obsidian vault) with a public-safe variant |
<!-- SKILLS_TABLE_END -->

Skills written by other people are **not copied here**. They are listed with links in [THIRD_PARTY.md](THIRD_PARTY.md).

## Install

Everything is plain files. Back up your own `~/.claude` first.

1. Copy what you want: `skills/*` to `~/.claude/skills/`, `agents/*.md` to `~/.claude/agents/`, `hooks/*` to `~/.claude/hooks/`, `scripts/*` to `~/.claude/scripts/`.
2. Merge `examples/settings.example.json` into `~/.claude/settings.json` (do not overwrite yours). Replace `<HOME>` with your home folder, for example `C:/Users/you`. The hooks need Node.js.
3. Optional: adapt `examples/CLAUDE.global.example.md` into your `~/.claude/CLAUDE.md`. It is my own policy (for example the git rules), so read it before copying.
4. Check the cost: `node ~/.claude/scripts/context-audit.mjs`, then `node ~/.claude/scripts/config-audit.mjs`.

Things to know before copying:
- **Windows only:** the settings example calls `skill-install-gate.ps1` through PowerShell. On macOS or Linux remove those two hook entries or port the gate, otherwise every Bash call errors.
- **Copy `scripts/` together with `hooks/`:** `hooks/plugin-hook.mjs` imports `scripts/plugin-toggle.mjs`.
- `plugin-hook.mjs` (the `TRIGGERS` list) and `plugin-toggle.mjs` (the `GROUPS` list) contain the plugin names I toggle; edit both to match yours.
- The example does not set `CLAUDE_CODE_SUBAGENT_MODEL`: the agent files already pin their own model.

## License

The files in this repository are MIT licensed (see `LICENSE`). Third-party skills linked from `THIRD_PARTY.md` keep their own licenses.

## Security notes

- Read every hook before enabling it: hooks run code on your machine. These ones use no network and no `eval`; `config-audit.mjs` checks your folder for both.
- A hook cannot load a plugin into a running session. `plugin-hook.mjs` only edits `settings.json`; you still run `/reload-plugins`.
- `skill-install-gate.ps1` matches command text. It can block a harmless command that merely mentions installing a plugin, and it fails open when it cannot parse its input or when the install command is not covered by its pattern. It is a seat belt, not a guarantee.
- The routes are a hypothesis built from published evidence and have not been proven on a benchmark. Treat them as a starting point.

## Maintenance

`scripts/sync-readme.mjs` mirrors only the skills authored here, refreshes the table above, refuses to commit if it finds secrets or personal data, and never pushes.
