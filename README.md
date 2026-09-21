# claude-skills

Custom [Claude Code](https://claude.com/claude-code) skills, agents, and commands I use day to day, mirrored from `~/.claude/`.

## skills/

| Skill | Purpose |
|---|---|
| `frontend-design` | Distinctive, non-generic frontend UI/visual design guidance |
| `graphify` | Turn any input (code, docs, papers, images, video) into a persistent, queryable knowledge graph |
| `humanizer` | Rewrite AI-sounding text so it reads naturally |
| `hyperframes` | Entry point for creating/editing/rendering HyperFrames videos and motion graphics |
| `hyperframes-animation` | Motion rules, scene blueprints, and runtime adapters (GSAP, Lottie, Three.js, etc.) |
| `hyperframes-audio` | Audio mixing for HyperFrames compositions (fades, ducking, effects, automation) |
| `hyperframes-cli` | HyperFrames CLI workflow: init, render, preview, publish, etc. |
| `hyperframes-core` | The HyperFrames composition contract (timing, tracks, deterministic render rules) |
| `hyperframes-creative` | Non-animation creative direction: palettes, typography, narration, beat planning |
| `hyperframes-keyframes` | Seek-safe camera moves, zooms, reframes, 2D/3D keyframe techniques |
| `hyperframes-registry` | Discover/install/wire pre-built HyperFrames blocks and components |
| `media-use` | Sourcing and generating media (BGM, SFX, voice, images, LUTs) for HyperFrames projects |
| `superdesign` | Design/redesign frontend UI on the Superdesign canvas |

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
