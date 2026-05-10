class StoryEngineError(Exception):
    """Base class for story engine failures."""


class StoryNotFoundError(StoryEngineError):
    """Raised when a story id cannot be loaded."""


class SceneAccessDeniedError(StoryEngineError):
    """Raised when a state tries to enter a scene whose conditions are not met."""


class InvalidChoiceError(StoryEngineError):
    """Raised when a choice is unknown or unavailable to the player."""
