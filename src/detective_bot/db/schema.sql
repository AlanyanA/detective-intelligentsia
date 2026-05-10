PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS player_states (
    user_id INTEGER NOT NULL,
    story_id TEXT NOT NULL,
    current_scene TEXT NOT NULL,
    visited_scenes TEXT NOT NULL,
    flags TEXT NOT NULL,
    inventory TEXT NOT NULL,
    discovered_clues TEXT NOT NULL,
    suspect_scores TEXT NOT NULL,
    endings_reached TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, story_id)
);

CREATE INDEX IF NOT EXISTS idx_player_states_user_updated
ON player_states (user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS analytics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    story_id TEXT NOT NULL,
    scene_id TEXT,
    choice_id TEXT,
    ending_id TEXT,
    payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analytics_story_event
ON analytics_events (story_id, event_type, created_at);

CREATE INDEX IF NOT EXISTS idx_analytics_scene
ON analytics_events (story_id, scene_id, created_at);
