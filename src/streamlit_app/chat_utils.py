import time


def get_avatar(role: str) -> str | None:
    if role == "user":
        return "🧑‍🎓"
    elif role == "assistant":
        return "🤖"
    return None


def stream_text_response(response: str):
    # Clean leading/trailing whitespace for better formatting
    response = response.strip()

    displayed_message = ""
    for char in response:
        displayed_message += char
        if char == "\n":
            time.sleep(0.06)  # Slightly longer pause on line breaks
        elif char == " ":
            time.sleep(0.03)  # Small pause for spaces
        else:
            time.sleep(0.004)  # Fast character output
        yield displayed_message + "▌"  # Typing indicator
    yield displayed_message  # Final message without cursor
