$raw = [Console]::In.ReadToEnd()
try { $cmd = ($raw | ConvertFrom-Json).tool_input.command } catch { exit 0 }
$install = 'skills(@\S+)?\s+add\b|plugins?\s+(install|add|marketplace\s+add)\b'
$scanned = '^\s*(SKILLS_SCANNED=1\s|\$env:SKILLS_SCANNED\s*=\s*[''"]?1[''"]?\s*;)'
if ($cmd -match $install -and $cmd -notmatch $scanned) {
  [Console]::Error.WriteLine("Blocked: skill/plugin install needs a security scan first. Clone the source to a temp dir, run the Docker SkillSpector scan AND a manual grep, report the verdict to the user, then re-run with the command starting with SKILLS_SCANNED=1 (PowerShell: `$env:SKILLS_SCANNED=1; <command>).")
  exit 2
}
exit 0
