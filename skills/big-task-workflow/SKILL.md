---
name: big-task-workflow
description: Use whenever the user asks to build or improve something (site, app, feature, integration, refactor, restructuring) or to investigate a complex system (e.g. an ML algorithm). Picks a route R0-R4 by task type and risk, from a direct fix up to a full plan/critic/review cycle, with a hard cap on agent calls. Single writer plus an executable check is the default; the full cycle is for high-risk work. A site always includes design and security.
---

# big-task-workflow (routes, capped)

Routes are a hypothesis from published evidence, not a proven result on this setup: a single writer with an executable check plus a fresh-context reviewer is the best-supported default; parallel agents pay off for research; planner/critic gains are weakly supported; multi-agent runs cost several times the tokens. Re-evaluate against `~/.claude/workflow-log.md` after ~10 logged tasks.

## 0. Step 0 and modes
Before spending tokens: one-line sanity check of the premise (is it flawed, risky or clearly worse than an alternative?). If so say so in 2-4 lines and wait. **"rápido"** = no subagents. **"completo"** = R4 with N=8.

## 1. Pick the route
**Closed risk list.** A hit means the change itself adds or modifies that behaviour, not that nearby code does it.
- **Hard hits => R4:** auth/sessions, secrets, payments, storing or handling personal data, deleting or overwriting data, production or irreversible changes.
- **Soft hits:** user input or forms, database/SQL, file or network I/O, dependencies. Small task (score N <= 2, see section 2): R1 plus a mandatory `reviewer` with the security lens. Otherwise R4.
- Torn between two routes, or unsure whether a risk applies: take the higher route.

- **R0 direct.** At most 1 file and ~20 lines, a one-sentence diff, AND no risk hit. Do it, run the check, 3-line report. No assessment.
- **R1 default** (build/improve in code you can read, no hard hit):
  - 5-line inline plan that names the check (test, build, lint, script, browser run). No executable check exists: write one first, or say plainly that none can run.
  - One writer (main thread, or one `implementer` for a separable chunk). Tests first for non-trivial logic.
  - The gate must actually run and its output is reported.
  - ONE fresh `reviewer` at the end only if the diff is over ~3 files or ~100 lines, or no executable check exists. It reads the diff against the requirements, not only the test result.
  - One-line `feature-assessment`. No planner, no critic.
  - **Sites and design:** single pass with `hallmark` + `frontend-design`, a binary rubric (CTA visible at 375 and 1280 px, no horizontal overflow, contrast, honest copy, security headers if deployed, no console errors or failed requests, LCP < 2.5 s, CLS < 0.1 and INP < 200 ms when measurable, keyboard path works; an automated accessibility pass covers only ~30-40% of WCAG, so never call a page "accessible" from it alone, and with no visual baseline say "inconclusive" instead of passing; never run mutating flows against production), one screenshot-against-rubric round, one fix. A form is a soft hit (R1 + security-lens reviewer when N <= 2); a backend, external API, personal data or other hard hit makes it R4.
- **R2 unfamiliar or uncertain** (new repo, "I can't yet say how it works"): `explorer` (haiku) reads first; short inline plan; a fresh `critic` only if multi-file or irreversible; then as R1. Full `feature-assessment` as the header. Do the find-skills check yourself, recommend at most one skill, never install without asking.
- **R3 research, investigation, feedback** ("improve this algorithm", "is there something better"): `researcher`s in PARALLEL (2-4 by breadth, 2 + N/2 paraphrased queries each, reuse what is known), then a detailed scored report with alternatives (feasibility %, security risk %, effort, uncertainty), then STOP and wait for approval before changing anything. After approval, build as R1/R2/R4.
- **R4 high stakes** (any risk hit, or N >= 4, or "completo"): the full cycle below.

Escalation: the gate fails twice, a critic/reviewer finds a high issue, or the diff outgrows its route => move up one route and announce it in one line. Announce the route up front too, with a recommended effort: "Route R1, effort medium, ~1 agent call. Say 'rápido' or 'completo' to change." Effort hypothesis: R0 low, R1 medium, R2 medium (high for large unfamiliar code), R3 medium, R4 high. Only the user can change the session effort (`/effort X`; do it before the task, since changing it mid-task breaks the prompt cache); subagent effort is fixed per agent file, so never promise to vary it per call.

## 2. R4 full cycle
Score N (0-8), +1 each: user data/auth/payments; backend or database; external APIs; several pages or modules; novel or research-heavy; >5 files in an existing codebase; production, irreversible or costly-if-wrong; high uncertainty.
Order: **assessment -> research -> plan -> critique -> build -> review.**
- **Hard cap: total agent calls <= 2 + N** (min 3). If the estimate is over 12, ask before starting.
- **Assessment:** `feature-assessment` skill in full.
- **Research:** ONE `researcher` call with 2 + N/2 paraphrased queries; reuse what is known; skip it when nothing is uncertain.
- **Plan:** N<=3 inline; N>=4 a `planner` capped at about 1 page at N<=3 and growing with N (an uncapped plan once cost ~89k tokens). Sites: includes design and security. Security risks stay as checklist items.
- **Critique:** fresh `critic`; add a round only while the last found high/medium issues, ceiling `1 + N/4` (max 3).
- **Build:** one `implementer` per independent part (never two writers on the same files); tests first for logic. Keep non-deliverables (plan, tests, notes) outside the folder that gets deployed.
- **Review:** fresh `reviewer` per lens, at most 2 rounds; re-review only lenses that found something.
- A high finding may add a round or lens up to the cap; beyond it, ask the user.
- **Dual review, only for serious security or payment work** (a hard hit on auth/sessions, payments, secrets or personal data, where an error is costly): TWO fresh `reviewer`s with different lenses (one attacker-minded security, one requirements/correctness), no shared context, BOTH must pass; fresh pair each round, max 3 rounds, then escalate to the user. Both are Claude, so independence is weaker than two different model families; say so in the report. It is exempt from the lens limit and the 2-round review limit; its calls are budgeted separately (up to 2 reviewers per round, 3 rounds, +6 calls), added on top of the cap and shown in the up-front estimate. Never use it for ordinary R1-R3 work.
- **Per call pass only `model`.** Effort comes from each agent's frontmatter.

## 3. Review lenses (a focus line in the prompt, not new files)
Max 1 lens at N<=2, 2 at N 3-5, 3 at N>=6. **Security is always a lens** for sites with forms or data, auth, user data and payments.
- **Security:** auth, input, secrets, rate limiting/DoS, dependencies, data exposure.
- **Design/UX:** hallmark slop-test, accessibility, responsive, honest copy. Sales sites add conversion and memorability: offer and CTA clear in 10 seconds, distinctive rather than merely safe.
- **Correctness/tests:** requirements, edge cases, regressions.
- **Silent failures:** swallowed errors, empty catch blocks, `.catch(() => [])`, ignored return codes, lost stack traces, fallbacks that hide a failure, no timeout or error handling around network/file/db calls, no rollback around transactions, success reported without checking.
- **Performance/scalability:** hot paths, queries, bundle size, load.
- **Data/ML validity:** leakage, eval protocol, baselines, reproducibility, metric fits the goal.
- **Cost/ops:** hosting, monitoring, rollback, ongoing cost.
- **Legal/privacy:** scraping ToS, LGPD, licenses.

## 4. Always
- Critic/reviewer filter: only correctness, missing requirements or security of medium+ severity, each with a concrete fix. They prefer executed evidence (tests, build, grep) to opinion and list what they could not verify.
- The author never reviews its own work. Subagents can't talk to each other: relay short summaries and keep your own context clean.
- The security scan of the diff before commits applies to every route, R0 included.
- The global `~/.claude/CLAUDE.md` wins over a project CLAUDE.md where they conflict.
- After an R2+ task, append one line to `~/.claude/workflow-log.md`: date | task | route | agent calls | gate result.
- Finish with a short report: what was done, what differs from the request and why, residual risks, what was verified (real command output).
