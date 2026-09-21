#!/usr/bin/env node
// Fires from a Claude Code PostToolUse(Write) hook whenever a SKILL.md is written.
// Mirrors ~/.claude/skills/ into this repo's skills/, regenerates the README table,
// and commits+pushes if anything changed.
import { readdirSync, statSync, readFileSync, writeFileSync, cpSync, rmSync, existsSync } from "node:fs";
import { join } from "node:path";
import { execSync } from "node:child_process";
import os from "node:os";

const triggerPath = (process.argv[2] || "").replace(/\\/g, "/");
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
  cpSync(join(SRC, name), join(DEST, name), { recursive: true, force: true });
}

function frontmatter(skillMdPath) {
  const text = readFileSync(skillMdPath, "utf8");
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return "";
  const body = m[1];
  const descLine = body.match(/^description:\s*(\|[-+]?|>[-+]?)?\s*(.*)$/m);
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

sh("git add -A");
sh(`git commit -q -m "Sync skills from ~/.claude/skills"`);
sh("git push -q");
