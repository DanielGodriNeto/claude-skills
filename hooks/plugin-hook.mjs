// mode "prompt" (UserPromptSubmit): the user explicitly asks to turn a plugin group on -> flip settings.json and tell the model to relay /reload-plugins.
// mode "session" (SessionStart, startup only): switch the on-demand groups back off so every new session starts lean.
import { readFileSync } from "node:fs";
import { setGroup } from "../scripts/plugin-toggle.mjs";

const mode = process.argv[2];
let input = {};
try { input = JSON.parse(readFileSync(0, "utf8")); } catch { process.exit(0); }

const ON = "lig(?:ue|a|ar)|ativ(?:e|ar)|habilit(?:e|ar)|enable|turn on|activate";
const TRIGGERS = {
  superpowers: new RegExp(`(?<!\\p{L})(?:${ON})\\s+(?:o\\s+|the\\s+)?superpowers(?!\\p{L})`, "iu"),
  engineering: new RegExp(`(?<!\\p{L})(?:${ON})\\s+(?:os\\s+|o\\s+|the\\s+)?(?:pacotes?\\s+|packs?\\s+|plugins?\\s+)?engineering(?!\\p{L})`, "iu"),
};
// A negation shortly before the match ("nao ligue o superpowers", "do not enable ...") cancels it.
const NEGATION = /(?:n[aã]o|nunca|sem|don'?t|do not|never|without)\b[^.!?\n]{0,25}$/iu;

function asked(re, prompt) {
  const m = re.exec(prompt);
  return Boolean(m) && !NEGATION.test(prompt.slice(Math.max(0, m.index - 30), m.index));
}

try {
  if (mode === "session") {
    for (const g of Object.keys(TRIGGERS)) setGroup(g, false);
    process.exit(0);
  }
  if (mode === "prompt") {
    const prompt = String(input.prompt || "");
    if (/task-notification|SYSTEM NOTIFICATION/i.test(prompt)) process.exit(0); // automated notices are not user requests
    const turnedOn = Object.keys(TRIGGERS).filter((g) => asked(TRIGGERS[g], prompt) && setGroup(g, true));
    if (!turnedOn.length) process.exit(0);
    const msg = `[plugins] Enabled in settings: ${turnedOn.join(", ")}. A hook cannot load plugins into a running session: tell the user to run /reload-plugins now (or restart). They switch back off automatically on the next new session.`;
    process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: "UserPromptSubmit", additionalContext: msg } }));
  }
} catch { process.exit(0); }
