from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from detective_bot.config import get_settings
from detective_bot.db import Database
from detective_bot.engine.story_loader import StoryLoader
from detective_bot.engine.validator import StoryValidator, ValidationReport


def main() -> None:
    parser = argparse.ArgumentParser(prog="detective")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate story content.")
    validate_parser.add_argument("story_id", nargs="?", help="Specific story id to validate.")
    validate_parser.add_argument("--stories-path", type=Path, default=None)

    subparsers.add_parser("init-db", help="Create SQLite tables.")

    args = parser.parse_args()
    if args.command == "validate":
        settings = get_settings()
        stories_path = args.stories_path or settings.stories_path
        raise SystemExit(_validate(stories_path, args.story_id))
    if args.command == "init-db":
        asyncio.run(_init_db())


def _validate(stories_path: Path, story_id: str | None) -> int:
    loader = StoryLoader(stories_path)
    validator = StoryValidator()
    story_ids = [story_id] if story_id else loader.list_story_ids()
    if not story_ids:
        print(f"No stories found in {stories_path}.")
        return 1

    reports: list[ValidationReport] = []
    for current_story_id in story_ids:
        try:
            reports.append(validator.validate(loader.load(current_story_id)))
        except Exception as exc:
            report = ValidationReport(story_id=current_story_id or "<unknown>")
            report.errors.append(str(exc))
            reports.append(report)

    for report in reports:
        status = "OK" if report.ok else "FAILED"
        print(f"[{status}] {report.story_id}")
        for error in report.errors:
            print(f"  ERROR: {error}")
        for warning in report.warnings:
            print(f"  WARN: {warning}")

    return 0 if all(report.ok for report in reports) else 1


async def _init_db() -> None:
    settings = get_settings()
    await Database(settings.sqlite_path).initialize()
    print(f"Initialized database at {settings.sqlite_path}")


if __name__ == "__main__":
    main()
