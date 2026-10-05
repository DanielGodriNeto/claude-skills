// Turns plugin groups on/off in ~/.claude/settings.json (enabledPlugins). Takes effect after /reload-plugins or a new session.
// CLI: node plugin-toggle.mjs on|off superpowers|engineering
import { readFileSync, writeFileSync, copyFileSync, renameSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const file = join(homedir(), ".claude", "settings.json");

export const GROUPS = {
  superpowers: ["superpowers@claude-plugins-official"],
  engineering: ["engineering-skills@claude-code-skills", "engineering-advanced-skills@claude-code-skills"],
};

// Atomic replace: write a temp file next to the target, then rename over it.
function writeAtomic(path, text) {
  const tmp = `${path}.tmp-toggle`;
  writeFileSync(tmp, text);
  try { renameSync(tmp, path); } catch { writeFileSync(path, text); }
}

// Returns true when settings.json was changed.
export function setGroup(group, on) {
  const keys = GROUPS[group];
  if (!keys) throw new Error(`unknown group: ${group}`);
  const settings = JSON.parse(readFileSync(file, "utf8"));
  const enabled = settings.enabledPlugins || {};
  const todo = keys.filter((k) => k in enabled && enabled[k] !== on);
  if (!todo.length) return false;
  if (!existsSync(`${file}.bak-toggle`)) copyFileSync(file, `${file}.bak-toggle`);
  for (const k of todo) enabled[k] = on;
  settings.enabledPlugins = enabled;
  writeAtomic(file, JSON.stringify(settings, null, 2) + "\n");
  return true;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [state, group] = process.argv.slice(2);
  if (!["on", "off"].includes(state) || !GROUPS[group]) {
    console.error("usage: node plugin-toggle.mjs on|off superpowers|engineering");
    process.exit(1);
  }
  console.log(setGroup(group, state === "on") ? `${group}: ${state} (run /reload-plugins to apply now)` : `${group}: already ${state}`);
}
