# Pitfalls (all happened once)

- A Python heredoc through the Bash tool turns `"\\n"` into a real line break. Use `chr(10)`, `splitlines()` or the Edit tool.
- Two jobs racing: the second ran on the trigger commit and its bot push was rejected. Give it `ref: main`.
- A fixed local port (8765) already served something else. Use a random high port and check what answers before opening it.
- A script named `ast.py` shadowed the stdlib `ast` module and broke Playwright. Never name scripts after stdlib modules.
- `range()` with a float in a line-drawing helper. Use `round()`.
- SVG text color overridden by a class rule. Use inline `style="fill:..."`.
- Grey route line unreadable on a snow-colored area. Use a dark blue plus a translucent strip behind it.
- A full-screen capture leaked the user's desktop (deleted before any use). Never capture the whole screen; see the capture section in `readme-design`.
- A local preview rewrote the tracked SVG with preview numbers. `git checkout` the file before committing.
- The user rejected procedural scenes and generated banners. When they have the image or a print, use theirs.
