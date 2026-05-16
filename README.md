# LLM Interactive Fiction World Engine

A local-only engine for interactive fiction where an LLM handles language-facing tasks and a deterministic world engine owns canonical state, rules, events, and saves.

This repository currently contains documentation and a minimal typed backend skeleton only.

## Planned Stack

- Backend: Python, FastAPI, SQLite
- Schemas: Pydantic
- Tests: pytest
- LLM: provider abstraction with credentials loaded from environment variables

