# TraceWeaver

> Linux-native local context infrastructure for AI coding agents.
> Captures shell / git / filesystem / browser / tmux activity, distills
> non-inferable conventions with a local SLM (OpenVINO / Ollama /
> llama.cpp / rules-only fallback), and renders 7 vendor-neutral output
> formats (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/*.mdc`, Codex
> `config.toml`, Aider conventions, `GEMINI.md`, `SKILL.md`) for
> selective or transactional all-apply.

100% local. SQLite + sqlite-vec. Python 3.12 / FastAPI / React 19.

This repository is in **early implementation**. The full design is in
[`docs/plan/`](docs/plan/) (19 documents, 28 000 lines, 15 ADRs locked).
Work logs in [`docs/work_log/`](docs/work_log/).

## Quick start (developer)

```bash
uv sync                     # creates .venv + installs all dev deps
uv run traceweaver-daemon   # starts the FastAPI daemon on 127.0.0.1:7777
# in another shell
cd ui && pnpm install && pnpm dev
# or, after building:
uv run tw open              # opens the bundled SPA in your browser
```

See [`docs/preset/`](docs/preset/) for the full preset bootstrap (apt
packages, Intel iGPU/NPU drivers, model conversion, systemd unit).

## License

Core (`src/traceweaver/`): MPL-2.0. Plugin surfaces (`ui/`,
`extensions/browser/`, `hooks/`): Apache-2.0. Docs (`docs/plan/`,
`docs/preset/`): CC BY 4.0. See `SUBLICENSES.md`.
