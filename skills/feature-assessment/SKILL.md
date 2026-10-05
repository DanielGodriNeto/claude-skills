---
name: feature-assessment
description: Use BEFORE building or changing something non-trivial (routes R2-R4 of big-task-workflow, or when the user asks for a verdict); in route R1 give only a one-line version, in R0 skip it. Applies to a new feature, site, app, integration or refactor. Gives an honest feasibility and risk assessment with percentages, reasons, a recommended approach and what is still uncertain. Reuses research already done in the session.
---

# feature-assessment

Give the user a short, honest verdict before any code. Max ~15 lines, in the user's language.

1. **Use what is already known.** Reuse research and decisions from this conversation; never tell the user "go research that". If a key fact is missing, research it yourself (`researcher` agent or WebSearch) and report it as "I checked X and found Y".
2. **Verdict table** (estimates, with the reason for each):
   - **Feasibility** (can it be done as asked): `NN%`, why.
   - **Chance of a security problem** (lower is better): `NN%`, why.
   - **Effort/cost** (small / medium / large, and token cost if big): why.
   - **Main uncertainty** and the cheapest way to resolve it (a quick spike or test).
3. **If it won't work as asked,** say so plainly: "This won't work this way because [reasons]. I recommend [approach] because [reasons]", with that approach's numbers too.
4. **Rules for the numbers:** they are calibrated estimates, never 0% or 100%. Say what drives each one and what would move it. "100% safe" is never true: state residual risks instead.
5. **Decision:** if feasibility is below 70% or the security risk is above 30%, stop and wait for the user. Otherwise proceed (large work goes to `big-task-workflow`) and keep this assessment as the header of the plan.
