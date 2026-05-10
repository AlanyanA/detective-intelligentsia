# Story Schema

Stories are content packages. The engine loads every story from `stories/<story_id>` and does not require Python changes for new cases.

```text
stories/
  case_001/
    story.yaml
    scenes/
      intro.yaml
      ...
    assets/
      ledger_fragment.txt
```

## Manifest: `story.yaml`

```yaml
id: case_001
title: The Last Telegram
version: 1.0.0
author: Your Studio
start_scene: intro
description: Short catalog text.
language: en
```

## Scene

```yaml
id: crime_scene
text: "Short Telegram-friendly scene text."
media:
  - kind: document
    path: assets/evidence.txt
    caption: Evidence
conditions:
  - flag: accepted_case
effects:
  set_flags:
    visited_crime_scene: true
  add_inventory:
    - brass_key
  remove_inventory:
    - sealed_envelope
  discover_clues:
    - ink_smear
  suspect_scores:
    mira: 2
choices:
  - id: inspect_body
    text: Inspect the body
    next_scene: body
    conditions:
      - not:
          clue: ink_smear
    effects:
      discover_clues:
        - torn_note
ending:
  id: case_closed
  title: Case Closed
  outcome: success
  completion: true
```

## Conditions

Conditions are data, never prose. They can be placed on scenes or choices.

Supported checks:

```yaml
- flag: body_examined
- flag: safe_opened
  equals: true
- flag: optional_branch_seen
  exists: false
- inventory: brass_key
- clue: ledger_fragment
- visited: crime_scene
- suspect_score: mira
  gte: 2
- suspect_score: doorman
  lte: 1
```

Boolean composition:

```yaml
- and:
    - clue: ledger_fragment
    - clue: mira_visit
- or:
    - inventory: brass_key
    - flag: safe_forced
- not:
    visited: safe
```

## Telegram UX Rules

Keep scene text short and punchy. Each scene supports at most four choices. Endings should have no choices; the Telegram adapter automatically offers Restart and Stories.

Choice ids are used in compact Telegram callbacks as `c:<choice_id>`, so each generated callback must fit Telegram's 64-byte limit. The validator checks this.

## Media

Media paths are relative to the story folder and validated so they cannot escape the package.

Supported media kinds:

- `image`
- `audio`
- `document`

## Adding A New Story

1. Create `stories/<new_story_id>/story.yaml`.
2. Add scene files under `stories/<new_story_id>/scenes`.
3. Put media under `stories/<new_story_id>/assets`.
4. Run `python -m detective_bot.cli validate <new_story_id>`.

No Python code changes are required.
