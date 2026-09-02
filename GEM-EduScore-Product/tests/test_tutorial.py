from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app


class TutorialVideoTests(unittest.TestCase):
    def test_finds_supported_tutorial_video(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tutorial_dir = Path(directory)
            expected = tutorial_dir / "tutorial.mp4"
            expected.touch()

            with patch.object(app, "TUTORIAL_DIR", tutorial_dir):
                self.assertEqual(app.tutorial_video_path(), expected)

    def test_prefers_web_optimized_video(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tutorial_dir = Path(directory)
            (tutorial_dir / "tutorial.mp4").touch()
            expected = tutorial_dir / "tutorial-web.mp4"
            expected.touch()

            with patch.object(app, "TUTORIAL_DIR", tutorial_dir):
                self.assertEqual(app.tutorial_video_path(), expected)


if __name__ == "__main__":
    unittest.main()
