// Measures the standing context cost of the Claude Code setup (rough: tokens ~ chars / 4).
// Counts only what loads: own skills/agents, ENABLED plugins (latest cached version), CLAUDE.md files.
// Usage: node ~/.claude/scripts/context-audit.mjs
import { readFileSync, readdirSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join, sep } from "node:path";

const root = join(homedir(), ".claude");
const tok = (s) => Math.ceil(s.length / 4);
const read = (p) => { try { return readFileSync(p, "utf8"); } catch { return ""; } };
const lines = (s) => (s ? s.split("\n").length : 0);
const rel = (p) => p.replace(root + sep, "");

function walk(dir, match, out = []) {
  let entries = [];
  try { entries = readdirSync(dir); } catch { return out; }
  for (const e of entries) {
    const p = join(dir, e);
    let st; try { st = statSync(p); } catch { continue; }
    if (st.isDirectory()) walk(p, match, out);
    else if (match(p)) out.push(p);
  }
  return out;
}

function frontmatter(text) {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return { name: "", description: "" };
  const get = (k) => (m[1].match(new RegExp(`^${k}:\\s*(.*)$`, "m")) || [, ""])[1].trim();
  return { name: get("name"), description: get("description") };
}

function latestVersionDir(dir) {
  let subs = [];
  try { subs = readdirSync(dir).filter((e) => statSync(join(dir, e)).isDirectory()); } catch { return null; }
  if (!subs.length) return null;
  subs.sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  return join(dir, subs[subs.length - 1]);
}

let settings = {};
try { settings = JSON.parse(read(join(root, "settings.json"))); } catch { /* ignore */ }
const plugins = Object.entries(settings.enabledPlugins || {}).filter(([, on]) => on).map(([k]) => k);

const rows = [];
const flags = [];
const add = (group, item, always, full, limit, fileLines, path) => {
  rows.push({ group, item, always, full });
  if (limit && fileLines > limit) flags.push({ size: fileLines, text: `${item}: ${fileLines} lines (limit ${limit}) ${rel(path)}` });
};
const addSkill = (group, f) => {
  const t = read(f);
  const fm = frontmatter(t);
  add(group, fm.name || rel(f), tok(`${fm.name} ${fm.description}`), tok(t), 400, lines(t), f);
};

// CLAUDE.md files load fully every session
for (const f of [join(root, "CLAUDE.md"), join(root, "RTK.md")]) {
  const t = read(f);
  if (t) add("memory", rel(f), tok(t), tok(t), f.endsWith("CLAUDE.md") ? 200 : 0, lines(t), f);
}

// Own skills: name + description preloaded, body only when invoked
for (const f of walk(join(root, "skills"), (p) => p.endsWith("SKILL.md"))) addSkill("skills: own", f);

// Enabled plugins: latest cached version only
const missing = [];
for (const key of plugins) {
  const [plugin, market] = key.split("@");
  if (!market) { missing.push(key); continue; }
  const base = latestVersionDir(join(root, "plugins", "cache", market, plugin));
  if (!base) { missing.push(key); continue; }
  const found = walk(base, (p) => p.endsWith("SKILL.md"));
  for (const f of found) addSkill(`plugin: ${plugin}`, f);
  for (const f of walk(join(base, "agents"), (p) => p.endsWith(".md"))) {
    const fm = frontmatter(read(f));
    add(`plugin: ${plugin}`, `agent ${fm.name}`, tok(`${fm.name} ${fm.description}`), tok(read(f)), 200, lines(read(f)), f);
  }
}

// Own agents: description preloaded into the Task tool list
for (const f of walk(join(root, "agents"), (p) => p.endsWith(".md"))) {
  const t = read(f);
  const fm = frontmatter(t);
  add("agents: own", fm.name || rel(f), tok(`${fm.name} ${fm.description}`), tok(t), 200, lines(t), f);
}

const hookCount = Object.values(settings.hooks || {}).flat().reduce((n, g) => n + (g.hooks || []).length, 0);
const groups = [...new Set(rows.map((r) => r.group))];
console.log("Standing context estimate (tokens ~ chars/4, approximate)\n");
console.log("group".padEnd(36) + "items".padStart(6) + "always-loaded".padStart(15) + "if all invoked".padStart(16));
for (const g of groups) {
  const items = rows.filter((r) => r.group === g);
  console.log(g.padEnd(36) + String(items.length).padStart(6) + String(items.reduce((n, r) => n + r.always, 0)).padStart(15) + String(items.reduce((n, r) => n + r.full, 0)).padStart(16));
}
console.log("\nTOTAL always-loaded: ~" + rows.reduce((n, r) => n + r.always, 0) + " tokens");
console.log(`Hooks configured: ${hookCount}. Enabled plugins (${plugins.length}).`);
if (missing.length) console.log(`Enabled but no cache folder found (not counted): ${missing.join(", ")}`);
console.log("Not counted: SessionStart text injected by plugins (e.g. superpowers, ponytail), MCP tool schemas (~500 tokens per tool), the system prompt.");

console.log("\nTop 10 always-loaded items:");
for (const r of [...rows].sort((a, b) => b.always - a.always).slice(0, 10)) console.log(`  ${String(r.always).padStart(6)}  ${r.group} / ${r.item}`);
console.log("\nLargest files over size limits (agent>200 lines, skill>400, CLAUDE.md>200), top 10 of " + flags.length + ":");
for (const f of flags.sort((a, b) => b.size - a.size).slice(0, 10)) console.log("  " + f.text);
