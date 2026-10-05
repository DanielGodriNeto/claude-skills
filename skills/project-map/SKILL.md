---
name: project-map
description: Use when the user asks to explain, understand, map, or get an overview of a project or codebase ("explain this project", "how does this repo work", "map the features"). Builds an Obsidian vault with one overview note per feature plus a graph of the code, so the user can browse the project visually.
---

# project-map

0. **Size gate (tokens):** if the project is small (about 30 files or fewer), skip the vault: read the README and key files and answer in a few lines, then offer the map. Run the full flow for non-trivial projects or when the user asks for a map/vault.

1. **Build the graph (cheap, local AST for code):** run the graphify skill on the project root with `--obsidian --obsidian-dir ~/vaults/<project-name>`. Skip if `~/vaults/<project-name>` is newer than the last commit.
2. **Write `~/vaults/<project-name>/00-Overview.md`** by hand from `graphify-out/GRAPH_REPORT.md` and the code:
   - 3-line purpose of the project and its stack.
   - One section per **feature** (not per file): plain-language explanation in 2-4 lines, the key files, and `[[wikilinks]]` to the matching graphify node notes.
   - "How the pieces connect" (short), "Risks / rough edges", "Where to start reading".
2b. **Two variants (public-safe).** The full vault stays private. Judge sensitivity: if any feature, endpoint, config, auth/payment/anti-abuse logic or internal detail could hurt the project in the wrong hands (someone wanting to sabotage it), build `~/vaults/<project-name>-public` that omits or generalizes those parts, and tell the user in chat what was left out (never write that list inside the public vault). If nothing is dangerous, say so: the public variant equals the full one. Only the public variant may go to a public repo.
3. **Reply in the chat in 5-8 lines**: what the project is, the 3-5 main features, and the path of the vault. Tell the user to open that folder as a vault in Obsidian and use Graph View; invite questions. Do not paste the whole overview.

4. **Offer to commit it** (ask once per project): in the same repo under `docs/project-map/` or in a separate repo, private or public. Public repos get only the public variant, scanned for secrets, tokens and internal paths first. Follow the global Git rules (commit locally; auto-push only if the repo is private and the change is small), and always ask before pushing it to a public repo.

Rules: keep notes factual (read the code, don't guess); build the vault only under `~/vaults`, and copy it into the repo (`docs/project-map/`) only if the user chooses to commit it; if the user has an existing vault, ask once for its path and reuse it.
