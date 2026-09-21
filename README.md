# claude-skills

Custom [Claude Code](https://claude.com/claude-code) skills, agents, and commands I use day to day, mirrored from `~/.claude/`.

## skills/

Auto-synced from `~/.claude/skills/` whenever a skill is added or edited — do not hand-edit the table below, it gets overwritten.

<!-- SKILLS_TABLE_START -->
| Skill | Purpose |
|---|---|
| `frontend-design` | Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making... |
| `graphify` | Use for any question about a codebase, its architecture, file relationships, or project content — especially when graphify-out/ exists, where the question sh... |
| `humanizer` | Use when editing or reviewing prose for inflated claims, sales language, vague sources, repetitive structure, stock AI words, passive voice, filler, or chatb... |
| `hyperframes` | video, animation, or motion graphic, including a promo, explainer, captioned clip, title card, overlay, slideshow or interactive deck, Remotion port, or any ... |
| `hyperframes-animation` | All animation knowledge for HyperFrames — atomic motion rules, multi-phase scene blueprints, scene transitions, broader motion-design techniques, AND the sev... |
| `hyperframes-audio` | fade-in/fade-out, crossfade, track gain or volume, volume automation, ducking, a music bed that fights a voiceover (voiceover carve), effects on a track (EQ,... |
| `hyperframes-cli` | compare, grade-compare, preview, play, present, beats, keyframes, single or batch render, publish, cloud, cloudrun, feedback, lambda, doctor, browser, info, ... |
| `hyperframes-core` | The HyperFrames composition contract — build one renderable project. Use for composition structure, the `data-*` timing attributes, `class="clip"`, tracks, s... |
| `hyperframes-creative` | Non-animation creative direction for HyperFrames videos. Use for design spec (frame.md / design.md) handling, palettes, typography, narration, beat planning,... |
| `hyperframes-keyframes` | Ken Burns treatment, camera move, visual match/whip handoff, or other seek-safe 2D/3D keyframes; also for GSAP, CSS keyframes, Anime.js, WAAPI, FLIP, paths, ... |
| `hyperframes-registry` | Search, install, and wire registry blocks and components into HyperFrames compositions. Use BEFORE hand-building any named visual — whenever a brief, a user,... |
| `media-use` | Agent Media OS, the single skill for every media need in a HyperFrames project. Resolve BGM, SFX, image, icon, brand logo, voice, color grade, or LUT into a ... |
| `superdesign` | Design or redesign frontend UI on the Superdesign canvas. Use whenever the user wants to design a page, feature, flow, or a brand-new product with no code ye... |
<!-- SKILLS_TABLE_END -->

## agents/

| Agent | Purpose |
|---|---|
| `code-architect` | Designs feature architectures from existing codebase patterns |
| `code-explorer` | Traces execution paths and maps architecture for a feature area |
| `code-reviewer` | Reviews code for bugs, security issues, and convention adherence |

## commands/

| Command | Purpose |
|---|---|
| `feature-dev` | Guided feature development with codebase understanding and architecture focus |

## Usage

Drop any of these into `~/.claude/skills/`, `~/.claude/agents/`, or `~/.claude/commands/` (or a project's `.claude/` equivalent) to enable them in Claude Code.

## External plugins (not mirrored here)

Installed via Claude Code's plugin marketplaces rather than authored locally, so they aren't copied into this repo — install them directly instead:

| Plugin | Source |
|---|---|
| `frontend-design` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| `superdesign` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| `feature-dev` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| `security-guidance` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| `superpowers` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| `semgrep` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) |
| `engineering-skills` | [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) |
| `engineering-advanced-skills` | [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) |
| `ui-ux-pro-max` | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) |
| `brag` | [latent-spaces/brag](https://github.com/latent-spaces/brag) |
| `ponytail` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) |
| `headroom` | [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) |
