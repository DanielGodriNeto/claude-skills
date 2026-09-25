## Sub-Agent Delegation & Context Economy

### Context Window Protection (Mandatory Sub-Agents)
The main session context is reserved strictly for high-level reasoning, architecture decisions, and direct user interaction. Never pollute the parent context with large file dumps, terminal output, or repetitive searches:
- **Mandatory Delegation Triggers:**
  - Exploring codebases or reading > 3 files to answer a question.
  - Parsing large test logs, stack traces, build artifacts, or terminal dumps.
  - Multi-file code reviews, security scans, or dependency audits.
  - Broad refactoring analysis or searching for patterns across the repo.
- **Synthesized Returns Only:** Sub-agents must execute the noise in their isolated context and return **only** a concise synthesis (findings, line numbers, or diff proposal) to the main thread.
- **Never Delegate:**
  - Single-file or single-location targeted edits.
  - Ambiguous requests (clarify first).
  - Destructive git operations (rebase, reset, hard clean).

### Model Routing & Cost Policy (Tiered Hierarchy)
Sub-agents must never run on expensive models for mechanical, repetitive, or exploratory tasks:
- **Main Session (Orchestrator):** Runs on the user's active model.
- **Sub-Agent Model Override:**
  - Whenever dispatching sub-agents via the `Agent` tool or defining custom agents, **ALWAYS** target cheaper models.
  - **`sonnet`:** For code generation, non-trivial debugging, refactoring, and test writing.
  - **`haiku`:** For file discovery, repo grepping, documentation checks, and log scanning.
  - **STRICT RULE:** Never spawn sub-agents with `model: inherit` (or by omitting the model field) when the main session is running on a more expensive model. Explicitly pin child workers to `sonnet` or `haiku` in their agent frontmatter.
