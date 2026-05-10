# Telegram Detective Engine

A production-oriented MVP for interactive detective fiction in Telegram. The bot is only a transport layer; all story logic lives in content packages under `stories/`.

## Architecture

```text
src/detective_bot/
  engine/          Universal story loading, conditions, rendering, validation
  models/          Pydantic/domain models
  db/              SQLite schema and repositories
  services/        Application orchestration, autosave, analytics
  telegram/        aiogram handlers, keyboards, media sender
  cli.py           Story validation and database tools
stories/
  case_001/        Example case, scenes, assets
  case_002/        Second case proving story extensibility
docs/
  story_schema.md
  analytics_queries.sql
```

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
python -m detective_bot.cli init-db
python -m detective_bot.cli validate
python -m detective_bot.main
```

Set `BOT_TOKEN` in `.env` before starting the bot.

## Commands

- `/start` opens the main menu.
- `/stories` lists available cases.
- `/continue` resumes the most recently played story.
- Inline buttons drive all scene choices.

## Story Content

New detective stories require no Python changes. Add a folder like:

```text
stories/case_002/
  story.yaml
  scenes/*.yaml
  assets/*
```

Then run:

```bash
python -m detective_bot.cli validate case_002
```

See [docs/story_schema.md](docs/story_schema.md) for the full schema.

## Database

SQLite stores:

- player state with current scene, visited scenes, flags, inventory, clues, suspect scores, endings, timestamps
- analytics events for scene visits, choices, endings, starts, continues, restarts

The schema is in `src/detective_bot/db/schema.sql`.

## Railway Deployment

1. Create a Railway project from this repository.
2. Add environment variables:
   - `BOT_TOKEN`
   - `DATABASE_URL=sqlite+aiosqlite:///./data/game.db`
   - `STORIES_PATH=./stories`
   - `LOG_LEVEL=INFO`
3. Deploy. Railway uses `railway.json` and starts `python -m detective_bot.main`.

For a larger production setup, mount persistent storage for `./data` or replace the repository layer with Postgres while keeping the engine unchanged.

## Future Extensions

The engine is transport-agnostic. A web frontend, Discord adapter, AI-assisted story generation, achievements, payments, or a story editor can call the same `GameService` and story content format.

The bundled `case_002` is intentionally different from `case_001` and uses nested conditions, separate flags, media, and endings to prove new stories can be added without changing core Python code.
