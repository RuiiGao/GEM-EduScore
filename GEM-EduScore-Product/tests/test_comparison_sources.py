from __future__ import annotations

import unittest
from unittest.mock import patch

import app


class FakeUpload:
    def __init__(self, name: str, content: bytes) -> None:
        self.name = name
        self._content = content

    def getvalue(self) -> bytes:
        return self._content


class ComparisonSourceTests(unittest.TestCase):
    def test_file_side_preserves_project_and_document_boundaries(self) -> None:
        material, info = app.extract_comparison_source(
            {
                "mode": "上传文件",
                "files": [FakeUpload("alpha.md", b"# Education\nInteractive workshop")],
                "wiki_url": "",
                "crawl_related": False,
                "max_pages": 1,
            },
            "A",
        )
        self.assertIn("PROJECT A", material)
        self.assertIn("alpha.md", material)
        self.assertEqual(info["name"], "alpha.md")

    @patch("app.cached_extract_wiki_material")
    def test_wiki_side_uses_same_extraction_contract(self, extractor) -> None:
        extractor.return_value = (
            "[WIKI PAGE]\nEducation evidence\n[/WIKI PAGE]",
            {"name": "Beta Wiki", "characters": 18, "words": 2, "lines": 1},
        )
        material, info = app.extract_comparison_source(
            {
                "mode": "分析 Wiki",
                "files": [],
                "wiki_url": "https://2025.igem.wiki/beta/education",
                "crawl_related": True,
                "max_pages": 6,
            },
            "B",
        )
        self.assertIn("PROJECT B", material)
        self.assertIn("Education evidence", material)
        self.assertEqual(info["name"], "Beta Wiki")
        extractor.assert_called_once_with("https://2025.igem.wiki/beta/education", True, 6)


if __name__ == "__main__":
    unittest.main()
