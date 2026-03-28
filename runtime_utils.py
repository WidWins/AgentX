from __future__ import annotations

import sys


def configure_utf8_stdio() -> None:
    """Use UTF-8 for terminal output when the stream supports reconfigure()."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue

        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower() == "utf-8":
            continue

        stream.reconfigure(encoding="utf-8")
