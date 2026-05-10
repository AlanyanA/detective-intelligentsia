MAX_CALLBACK_DATA_BYTES = 64


def callback_data(prefix: str, value: str | None = None) -> str:
    data = prefix if value is None else f"{prefix}:{value}"
    if len(data.encode("utf-8")) > MAX_CALLBACK_DATA_BYTES:
        raise ValueError(f"Telegram callback_data exceeds {MAX_CALLBACK_DATA_BYTES} bytes: {data}")
    return data


def story_callback(story_id: str) -> str:
    return callback_data("s", story_id)


def choice_callback(choice_id: str) -> str:
    return callback_data("c", choice_id)


CONTINUE_CALLBACK = "continue"
RESTART_CALLBACK = "r"
STORIES_CALLBACK = "stories"
