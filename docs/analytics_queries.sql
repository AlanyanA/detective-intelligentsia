-- Choice popularity
SELECT story_id, scene_id, choice_id, COUNT(*) AS selections
FROM analytics_events
WHERE event_type = 'choice_selected'
GROUP BY story_id, scene_id, choice_id
ORDER BY selections DESC;

-- Drop-off approximation: last scene visit per player/story
WITH last_visits AS (
    SELECT user_id, story_id, MAX(created_at) AS last_seen
    FROM analytics_events
    WHERE event_type = 'scene_visit'
    GROUP BY user_id, story_id
)
SELECT e.story_id, e.scene_id, COUNT(*) AS players_last_seen_here
FROM analytics_events e
JOIN last_visits l
  ON e.user_id = l.user_id
 AND e.story_id = l.story_id
 AND e.created_at = l.last_seen
GROUP BY e.story_id, e.scene_id
ORDER BY players_last_seen_here DESC;

-- Completion rate by story
WITH starters AS (
    SELECT story_id, COUNT(DISTINCT user_id) AS started
    FROM analytics_events
    WHERE event_type = 'story_started'
    GROUP BY story_id
),
finishers AS (
    SELECT story_id, COUNT(DISTINCT user_id) AS completed
    FROM analytics_events
    WHERE event_type = 'ending_reached'
    GROUP BY story_id
)
SELECT s.story_id,
       s.started,
       COALESCE(f.completed, 0) AS completed,
       ROUND(COALESCE(f.completed, 0) * 100.0 / s.started, 2) AS completion_rate_percent
FROM starters s
LEFT JOIN finishers f ON f.story_id = s.story_id;

-- Ending distribution
SELECT story_id, ending_id, COUNT(*) AS count
FROM analytics_events
WHERE event_type = 'ending_reached'
GROUP BY story_id, ending_id
ORDER BY count DESC;
