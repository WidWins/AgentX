import os
import unittest
import uuid
from pathlib import Path

from env_loader import load_env_file, load_first_env_file


class EnvLoaderTests(unittest.TestCase):
    def _create_env_file(self, content: str) -> Path:
        tmp_dir = Path("tests/.tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        env_path = tmp_dir / f"{uuid.uuid4().hex}.env"
        env_path.write_text(content, encoding="utf-8")
        return env_path

    def test_loads_values_from_env_file(self) -> None:
        env_path = self._create_env_file(
            "# comment\n"
            "LIVEKIT_URL=wss://example.livekit.cloud\n"
            "LIVEKIT_API_KEY='abc123'\n"
            "export LIVEKIT_API_SECRET=\"secret\"\n"
        )

        original = dict(os.environ)
        try:
            os.environ.pop("LIVEKIT_URL", None)
            os.environ.pop("LIVEKIT_API_KEY", None)
            os.environ.pop("LIVEKIT_API_SECRET", None)

            load_env_file(env_path)

            self.assertEqual(os.environ["LIVEKIT_URL"], "wss://example.livekit.cloud")
            self.assertEqual(os.environ["LIVEKIT_API_KEY"], "abc123")
            self.assertEqual(os.environ["LIVEKIT_API_SECRET"], "secret")
        finally:
            os.environ.clear()
            os.environ.update(original)
            env_path.unlink(missing_ok=True)

    def test_does_not_override_existing_environment_variable(self) -> None:
        env_path = self._create_env_file("LIVEKIT_URL=wss://new-value.livekit.cloud\n")

        original = dict(os.environ)
        try:
            os.environ["LIVEKIT_URL"] = "wss://existing.livekit.cloud"

            load_env_file(env_path)

            self.assertEqual(os.environ["LIVEKIT_URL"], "wss://existing.livekit.cloud")
        finally:
            os.environ.clear()
            os.environ.update(original)
            env_path.unlink(missing_ok=True)

    def test_load_first_env_file_uses_first_existing_path(self) -> None:
        env_path = self._create_env_file("LIVEKIT_URL=wss://first.livekit.cloud\n")
        missing_path = Path("tests/.tmp/does-not-exist.env")

        original = dict(os.environ)
        try:
            os.environ.pop("LIVEKIT_URL", None)

            loaded_path = load_first_env_file((missing_path, env_path))

            self.assertEqual(loaded_path, env_path)
            self.assertEqual(os.environ["LIVEKIT_URL"], "wss://first.livekit.cloud")
        finally:
            os.environ.clear()
            os.environ.update(original)
            env_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
