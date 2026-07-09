import tempfile
import unittest
from pathlib import Path

from tools import build_site


class BuildSiteTest(unittest.TestCase):
    def test_build_site_renders_reader_shell_and_markdown_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markdown_path = root / "sample.md"
            markdown_path.write_text(
                "\ufeff# Agent 橙皮书：测试版\n\n"
                "> 非官方开源指南 · 持续更新版\n\n"
                "| 版本 | 最后校验 |\n"
                "| --- | --- |\n"
                "| v0.1.0 | 2026-07-09 |\n\n"
                "## 目录\n\n"
                "- [0. 使用说明](#0-使用说明)\n\n"
                "## 0. 使用说明\n\n"
                "### 0.1 重要声明\n\n"
                "- 第一项\n"
                "- 第二项\n\n"
                "![流程图](assets/images/demo.png)\n\n"
                "```Plain Text\n"
                "Agent 任务模板\n"
                "```\n",
                encoding="utf-8",
            )

            build_site.build_site(markdown_path, root)
            index_html = (root / "index.html").read_text(encoding="utf-8")

            self.assertIn('class="book-shell"', index_html)
            self.assertIn('<h1 id="agent-橙皮书测试版">Agent 橙皮书：测试版</h1>', index_html)
            self.assertIn('class="toc-panel"', index_html)
            self.assertIn('<table>', index_html)
            self.assertIn('<figure class="book-figure">', index_html)
            self.assertIn('src="assets/images/demo.png"', index_html)
            self.assertIn('href="#0-使用说明"', index_html)
            self.assertIn('<pre><code class="language-plain-text">', index_html)
            self.assertNotIn("<p>﻿# Agent", index_html)
            self.assertNotIn("| 版本 |", index_html)

    def test_build_site_writes_all_public_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markdown_path = root / "sample.md"
            markdown_path.write_text("# Agent 橙皮书\n\n## 0. 使用说明\n\n正文\n", encoding="utf-8")

            build_site.build_site(markdown_path, root)

            self.assertTrue((root / "index.html").exists())
            self.assertTrue((root / "book.html").exists())
            self.assertTrue((root / "cover.html").exists())
            self.assertIn("在线阅读", (root / "cover.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
