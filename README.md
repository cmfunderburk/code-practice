# Code Practice

A tablet-first app for studying **whole programs**. You read a program through, then drill it
one unit at a time. You see a unit's cue and its shape as placeholder bars, write the code out
in your head, and reveal it line by line with a tap to check yourself. Tap a line you got wrong
to flag it, then redo the flagged units until each run is clean.

Every program comes in **Python, Rust and C**. Python is the entry point, and the Rust and C
ports are the same design written naturally in each language. Use them as comparison cases, or
study them for real if you're moving from Python toward systems languages. Each program also
comes with:

- **Spec:** the contract every language meets;
- **Problem** and **Notes**, per language: the API, the design chosen and the shapes rejected,
  and what the idea grows into at scale;
- **Defense:** questions to answer aloud about the design, with folded answers and a prompt for
  rehearsing them with an LLM.

The aim is to know a handful of well-shaped programs by heart, and to be able to say why they
are shaped that way.

## Drilling

From a program's page you can:

- **Drill whole program**, which runs every unit in order and ends with a table of results;
- tap one unit in the outline to drill just that unit;
- **Redo flagged**, which runs only the units whose last pass had misses.

A unit is finished when its last line is revealed, and the pass is saved at that point.

| Touch | Keyboard | Action |
|---|---|---|
| tap the right two-thirds | `space` | reveal the next step |
| tap the left third | `backspace` | hide the last step |
| long-press | | reveal the rest of the current block |
| tap a revealed line's gutter | `m` (last step) | flag or unflag it as missed |
| swipe left / right | `→` / `←` | next / previous unit |
| **Reset** | `r` | hide everything and clear this pass's flags |
| **Signature** | `s` | show the unit's first line (`def ...`) as given |
| | `enter` / `escape` | next unit once finished / back to the program |

Settings cover the signature default, font size, theme, and swapping the tap zones for
left-handed use.

## The programs

| Tier | Program | Pattern |
|---|---|---|
| easy | Hangman | functional core, imperative shell |
| easy | Roman Numerals | table-driven render and parse |
| easy | Tic-Tac-Toe | rules as pure board predicates |
| medium | Game of Life | sparse set of live cells |
| medium | Expression Calculator | tokenize, parse to an AST, evaluate |
| medium | Adventure Rooms | verb dispatch table |
| medium | Editor Buffer | command objects with undo and redo |
| hard | Logo Interpreter | parsed commands, executed with undo |

### Adding programs

The corpus format is described in [`corpus/README.md`](corpus/README.md). The repo ships a
[Claude Code](https://claude.com/claude-code) skill, `.claude/skills/add-program/`, that walks an
agent through a new program in order: the spec, the Python implementation and its cues, the Rust
and C ports, the documents, and the checks. In Claude Code, ask for a new program ("add a
Minesweeper program to the corpus") and it will follow the skill.

## Running it

Requires [Bun](https://bun.com) and [uv](https://docs.astral.sh/uv/).

```bash
bun install --frozen-lockfile
uv sync
bun run dev       # dev server with hot reload on 127.0.0.1:5419
bun run start     # production build, with the service worker for offline use
bun run verify    # typecheck + app tests + corpus tests
```

At startup the server builds the content bundle from `corpus/` (`scripts/build_bundle.py` →
`src/generated/bundle.json`), so restart it to pick up corpus changes. An open app then offers
"A new version is ready · Reload". `bun run bundle` rebuilds the bundle by hand.

### On a tablet

The server listens on loopback only. To use the app on an iPad or another tablet, put it behind
something that serves HTTPS on your network. The service worker needs a secure origin. With
[Tailscale](https://tailscale.com):

```bash
bun run ipad                         # production mode, restarting on file changes
tailscale serve --bg --https=8443 5419
# open https://<host>.<tailnet>.ts.net:8443/ on the tablet, then Share → Add to Home Screen
tailscale serve --https=8443 off     # stop sharing
```

After the first visit, the app works offline. The service worker keeps the app, and the corpus
ships inside it. Drill history stays on the device. **Backup**, at the bottom of the library,
exports your history and settings as a JSON file and restores them.

The built app contains the whole corpus. If you build it from a private corpus of your own
(`CODE_PRACTICE_CORPUS=/path/to/corpus`), don't host it publicly.

## Acknowledgments

Several program ideas were inspired by Al Sweigart's free books
[*The Big Book of Small Python Projects*](https://inventwithpython.com/bigbookpython/) and
[*Python Programming Exercises, Gently Explained*](https://inventwithpython.com/pythongently/).
The implementations and documents here are original.

## License

[MIT](LICENSE)
