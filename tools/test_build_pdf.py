import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from tools import build_pdf


class BuildPdfTest(unittest.TestCase):
    def test_build_pdf_starts_with_agent_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markdown_path = root / "sample.md"
            output_pdf = root / "sample.pdf"
            markdown_path.write_text(
                "# 正文标题\n\n这是正文第一页。\n\n## 小节\n\n- 第一项\n- 第二项\n",
                encoding="utf-8",
            )

            build_pdf.build_pdf(markdown_path, output_pdf, title="Agent 橙皮书")

            reader = PdfReader(output_pdf)
            self.assertGreaterEqual(len(reader.pages), 2)
            cover_text = reader.pages[0].extract_text()
            body_text = "\n".join(page.extract_text() for page in reader.pages[1:])

            self.assertIn("Agent 橙皮书", cover_text)
            self.assertIn("正文标题", body_text)


if __name__ == "__main__":
    unittest.main()
