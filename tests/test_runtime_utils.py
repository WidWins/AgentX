import sys
import unittest
from unittest.mock import patch

from runtime_utils import configure_utf8_stdio


class _DummyStream:
    def __init__(self, encoding: str | None) -> None:
        self.encoding = encoding
        self.reconfigure_calls: list[str] = []

    def reconfigure(self, *, encoding: str) -> None:
        self.reconfigure_calls.append(encoding)
        self.encoding = encoding


class RuntimeUtilsTests(unittest.TestCase):
    def test_reconfigures_non_utf8_stdio_streams(self) -> None:
        stdout = _DummyStream("cp1252")
        stderr = _DummyStream("ascii")

        with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
            configure_utf8_stdio()

        self.assertEqual(stdout.reconfigure_calls, ["utf-8"])
        self.assertEqual(stderr.reconfigure_calls, ["utf-8"])

    def test_skips_streams_already_using_utf8(self) -> None:
        stdout = _DummyStream("utf-8")
        stderr = _DummyStream("UTF-8")

        with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
            configure_utf8_stdio()

        self.assertEqual(stdout.reconfigure_calls, [])
        self.assertEqual(stderr.reconfigure_calls, [])


if __name__ == "__main__":
    unittest.main()
