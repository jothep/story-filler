"""Keep untrusted fields readable within a single plain-text log entry."""


def escape_log_value(value):
    """Escape controls without changing printable text or the original value."""
    # Escape literal backslashes first so an actual newline remains distinguishable
    # from the two printable characters ``\n`` supplied by a caller.
    text = str(value).replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")
    # Include terminal controls, Unicode line separators and bidi controls.
    return "".join(char if char.isprintable() else ascii(char)[1:-1] for char in text)
