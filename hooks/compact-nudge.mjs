import { readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const FIRST = 50; // first nudge after this many tool calls, then every STEP
const STEP = 25;

let input = {};
try { input = JSON.parse(readFileSync(0, "utf8")); } catch { process.exit(0); }
const session = String(input.session_id || "").replace(/[^\w-]/g, "");
if (!session) process.exit(0);

const file = join(tmpdir(), `claude-compact-nudge-${session}.txt`);
let count = 0;
try { count = parseInt(readFileSync(file, "utf8"), 10) || 0; } catch { /* first call */ }
count += 1;
try { writeFileSync(file, String(count)); } catch { process.exit(0); }

if (count < FIRST || (count - FIRST) % STEP !== 0) process.exit(0);

const msg = `[context] ${count} tool calls in this session. Context is probably large. At the next phase boundary (never mid-implementation) tell the user to run /compact (keep modified files, test commands and open decisions), or /clear if the next task is unrelated (/handoff first if it must continue this work).`;
process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: msg } }));
