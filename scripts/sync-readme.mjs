#!/usr/bin/env node
// Fires from a Claude Code PostToolUse(Write) hook whenever a SKILL.md is written.
// Mirrors ~/.claude/skills/ into this repo's skills/, regenerates the README table,
// and commits locally if anything changed (push is manual).
import { readdirSync, statSync, readFileSync, writeFileSync, cpSync, rmSync, existsSync } from "node:fs";
import { join } from "node:path";
import { execSync } from "node:child_process";
import os from "node:os";

// argv[2] lets this be invoked directly for testing; normally reads the
// PostToolUse hook's stdin JSON ({ tool_input: { file_path }, tool_response: { filePath } }).
let rawPath = process.argv[2];
if (!rawPath) {
  const stdin = readFileSync(0, "utf8");
  const hook = JSON.parse(stdin || "{}");
  rawPath = hook?.tool_response?.filePath || hook?.tool_input?.file_path || "";
}
const triggerPath = rawPath.replace(/\\/g, "/");
if (!/\.claude\/skills\/.*SKILL\.md$/i.test(triggerPath)) process.exit(0);

const HOME = os.homedir();
const SRC = join(HOME, ".claude", "skills");
const REPO = join(HOME, "claude-skills");
const DEST = join(REPO, "skills");
const SKIP = new Set(["synced", ".trash"]); // Claude-managed, not user-authored

function skillDirs(root) {
  return readdirSync(root)
    .filter((name) => !SKIP.has(name) && statSync(join(root, name)).isDirectory())
    .sort();
}

// mirror SRC -> DEST (add/update/remove)
const srcDirs = new Set(skillDirs(SRC));
if (existsSync(DEST)) {
  for (const name of skillDirs(DEST)) {
    if (!srcDirs.has(name)) rmSync(join(DEST, name), { recursive: true, force: true });
  }
}
for (const name of srcDirs) {
  // skills installed with `npx skills add` are symlinks into ~/.agents/skills; copy their contents, not the link
  cpSync(join(SRC, name), join(DEST, name), { recursive: true, force: true, dereference: true });
}

function frontmatter(skillMdPath) {
  const text = readFileSync(skillMdPath, "utf8");
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return "";
  const body = m[1];
  const descLine = body.match(/^description:[ \t]*(\|[-+]?|>[-+]?)?[ \t]*(.*)$/m);
  if (!descLine) return "";
  let desc;
  if (descLine[1]) {
    // block scalar: collect indented continuation lines
    const after = body.slice(body.indexOf(descLine[0]) + descLine[0].length).split(/\r?\n/);
    const collected = [];
    for (const line of after) {
      if (/^\s+\S/.test(line)) collected.push(line.trim());
      else if (line.trim() === "") continue;
      else break;
    }
    desc = collected.join(" ");
  } else {
    desc = descLine[2].trim();
  }
  desc = desc.replace(/^["']|["']$/g, "").replace(/\|/g, "/").trim();
  return desc.length > 160 ? desc.slice(0, 157) + "..." : desc;
}

const rows = [...srcDirs].map((name) => {
  const skillMd = join(DEST, name, "SKILL.md");
  const desc = existsSync(skillMd) ? frontmatter(skillMd) : "";
  return `| \`${name}\` | ${desc || "—"} |`;
});

const table = ["| Skill | Purpose |", "|---|---|", ...rows].join("\n");

const readmePath = join(REPO, "README.md");
const readme = readFileSync(readmePath, "utf8");
const updated = readme.replace(
  /<!-- SKILLS_TABLE_START -->[\s\S]*?<!-- SKILLS_TABLE_END -->/,
  `<!-- SKILLS_TABLE_START -->\n${table}\n<!-- SKILLS_TABLE_END -->`
);
if (updated === readme) process.exit(0); // marker missing or no textual change to README itself
writeFileSync(readmePath, updated);

const sh = (cmd) => execSync(cmd, { cwd: REPO, stdio: "pipe" }).toString();

if (sh("git status --porcelain").trim() === "") process.exit(0);

// Safety gate: never publish secrets or personal data. Aborts before commit/push.
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const LEAK = new RegExp(
  [
    "sk-ant-[A-Za-z0-9_-]{10,}", "ghp_[A-Za-z0-9]{20,}", "gho_[A-Za-z0-9]{20,}", "github_pat_[A-Za-z0-9_]{20,}",
    "AKIA[0-9A-Z]{16}", "AIza[0-9A-Za-z_-]{30,}", "xox[bp]-[0-9A-Za-z-]+", "-----BEGIN [A-Z ]*PRIVATE KEY-----",
    esc(HOME), esc(HOME.replace(/\\/g, "/")), // personal home path, computed at runtime
  ].join("|")
);
function findLeaks(dir, hits = []) {
  for (const name of readdirSync(dir)) {
    if (name === ".git") continue;
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) findLeaks(p, hits);
    else if (st.size < 2_000_000 && LEAK.test(readFileSync(p, "utf8"))) hits.push(p);
  }
  return hits;
}
const leaks = findLeaks(REPO);
if (leaks.length) {
  writeFileSync(join(HOME, ".claude", "sync-blocked.log"), `${new Date().toISOString()} sync blocked, possible secret/personal data in:\n${leaks.join("\n")}\n`);
  process.exit(1);
}

sh("git add -A");
sh(`git commit -q -m "Sync skills from ~/.claude/skills"`);
// Publishing is manual on purpose: review, then run `git push` yourself.
