// Local, offline audit of ~/.claude for risky settings, injection text, hidden characters and secrets. No network, no LLM, 0 tokens.
// Scope: settings.json, CLAUDE.md, RTK.md, own agents/skills text, own hooks/ and scripts/. Third-party skill code is covered by SkillSpector at install time.
// Cache: if the config hash is unchanged since the last CLEAN scan it exits early. Use --force to rescan.
// Usage: node ~/.claude/scripts/config-audit.mjs [--force]
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync, writeFileSync, mkdirSync, lstatSync } from "node:fs";
import { homedir } from "node:os";
import { join, relative, basename } from "node:path";

const root = join(homedir(), ".claude");
const stateFile = join(root, "scan", "config-audit-state.json");
const force = process.argv.includes("--force");
const SELF = "config-audit.mjs";

function walk(dir, out = []) {
  let names = [];
  try { names = readdirSync(dir); } catch { return out; }
  for (const n of names) {
    const p = join(dir, n);
    let st; try { st = lstatSync(p); } catch { continue; }
    if (st.isSymbolicLink()) continue;
    if (st.isDirectory()) walk(p, out);
    else if (/\.(md|mjs|js|json|ps1|sh|yaml|yml)$/.test(n) && st.size < 300000) out.push(p);
  }
  return out;
}

// Zero-width and bidirectional control characters, compared by code point (this file stays pure ASCII).
function hasHiddenChar(line) {
  for (const c of line) {
    const n = c.codePointAt(0);
    if ((n >= 0x200b && n <= 0x200f) || (n >= 0x202a && n <= 0x202e) || n === 0x2060 || (n >= 0x2066 && n <= 0x2069)) return true;
  }
  return false;
}

const files = [
  join(root, "settings.json"), join(root, "CLAUDE.md"), join(root, "RTK.md"),
  ...walk(join(root, "agents")), ...walk(join(root, "skills")), ...walk(join(root, "hooks")), ...walk(join(root, "scripts")),
].filter((p) => { try { return statSync(p).isFile(); } catch { return false; } });

const texts = new Map(files.map((p) => [p, readFileSync(p, "utf8")]));
const hash = createHash("sha256");
for (const p of [...texts.keys()].sort()) hash.update(relative(root, p) + "\0" + texts.get(p) + "\0");
const digest = hash.digest("hex");

let state = {};
try { state = JSON.parse(readFileSync(stateFile, "utf8")); } catch { /* first run */ }
if (!force && state.hash === digest && state.findings === 0) {
  console.log(`Config unchanged since the last clean scan (${state.date}, ${files.length} files). Nothing to do. Use --force to rescan.`);
  process.exit(0);
}

const findings = [];
const flag = (sev, file, line, msg) => findings.push({ sev, where: `${relative(root, file)}${line ? ":" + line : ""}`, msg });

// A quoted mention ("ignore previous instructions" as something to grep for) is not an injection.
const RULES = [
  { sev: "HIGH", re: /ignore (all )?(previous|prior|above) (instructions|rules)|disregard (the )?(system|previous) (prompt|instructions)|you are now (in )?(dan|developer mode)/i, skip: /["'`]\s*(ignore|disregard)/i, msg: "prompt-injection phrase" },
  { sev: "HIGH", test: hasHiddenChar, msg: "hidden zero-width or bidi character" },
  { sev: "HIGH", re: /(sk-ant-|ghp_|github_pat_|AKIA[0-9A-Z]{16}|xox[baprs]-)[A-Za-z0-9_-]{8,}/, msg: "looks like a secret or token" },
  { sev: "MEDIUM", re: /[A-Za-z0-9+/=]{300,}/, msg: "long base64-like blob" },
];
const CODE_RULES = [
  { sev: "HIGH", re: /\beval\s*\(|new Function\s*\(|Invoke-Expression/i, msg: "dynamic code execution" },
  { sev: "HIGH", re: /(curl|wget)[^\n|]*\|\s*(sh|bash|pwsh|powershell)/i, msg: "download piped to a shell" },
  { sev: "MEDIUM", re: /\b(Invoke-WebRequest|curl|wget)\b|https?:\/\/(?!localhost|127\.0\.0\.1)/i, msg: "network access in a hook or script" },
];

for (const [p, text] of texts) {
  if (basename(p) === SELF) continue;
  const isOwnCode = /^(hooks|scripts)[\\/]/.test(relative(root, p));
  const rules = isOwnCode ? [...RULES, ...CODE_RULES] : RULES;
  text.split("\n").forEach((l, i) => {
    for (const r of rules) {
      const hit = r.test ? r.test(l) : r.re.test(l);
      if (hit && !(r.skip && r.skip.test(l))) flag(r.sev, p, i + 1, r.msg);
    }
  });
}

// settings.json checks
const settingsFile = join(root, "settings.json");
try {
  const s = JSON.parse(texts.get(settingsFile));
  if (s.permissions && s.permissions.defaultMode === "bypassPermissions") flag("HIGH", settingsFile, 0, "defaultMode is bypassPermissions");
  if (s.skipDangerousModePermissionPrompt) flag("HIGH", settingsFile, 0, "skipDangerousModePermissionPrompt is on");
  const allow = (s.permissions && s.permissions.allow) || [];
  for (const a of allow) if (/^(\*|Bash|Bash\(\*\)|PowerShell|PowerShell\(\*\)|Write|Edit)$/.test(a)) flag("HIGH", settingsFile, 0, `very broad allow rule: ${a}`);
  for (const [k, v] of Object.entries(s.env || {})) if (/KEY|TOKEN|SECRET|PASSWORD/i.test(k) && v) flag("HIGH", settingsFile, 0, `secret-like env var in settings: ${k}`);
  for (const g of Object.values(s.hooks || {}).flat()) for (const h of g.hooks || []) {
    if (/\b(curl|wget|Invoke-WebRequest|iwr|certutil|bitsadmin)\b|base64|http:\/\//i.test(h.command || "")) flag("MEDIUM", settingsFile, 0, `hook command touches network or encoding: ${String(h.command).slice(0, 90)}`);
  }
  for (const [name, m] of Object.entries(s.extraKnownMarketplaces || {})) {
    const src = m.source || {};
    flag("INFO", settingsFile, 0, `third-party marketplace '${name}': ${src.repo || src.path || src.source}`);
  }
} catch { flag("HIGH", settingsFile, 0, "settings.json is not valid JSON"); }

const order = { HIGH: 0, MEDIUM: 1, INFO: 2 };
findings.sort((a, b) => order[a.sev] - order[b.sev]);
const real = findings.filter((x) => x.sev !== "INFO").length;
console.log(`Scanned ${files.length} files. Findings: ${real} (+${findings.length - real} info). Triage each one: static rules are noisy.`);
for (const x of findings.slice(0, 40)) console.log(`  ${x.sev.padEnd(6)} ${x.where}  ${x.msg}`);
if (findings.length > 40) console.log(`  ... ${findings.length - 40} more`);

try {
  mkdirSync(join(root, "scan"), { recursive: true });
  writeFileSync(stateFile, JSON.stringify({ hash: digest, date: new Date().toISOString().slice(0, 10), findings: real }, null, 2));
} catch { /* cache is optional */ }
console.log(real === 0 ? "Clean: result cached; the next run exits early until a file changes." : "Not cached (findings present): it will rescan next time.");
