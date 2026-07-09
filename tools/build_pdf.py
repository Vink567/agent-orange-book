#!/usr/bin/env python3
"""Build a PDF edition with a full first-page cover image."""

from __future__ import annotations

import argparse
import html
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from build_site import DEFAULT_MARKDOWN, ROOT, metadata_from_markdown, render_markdown

DEFAULT_COVER = ROOT / "\u56fe\u7247\u548c\u9644\u4ef6" / "agent-orange-book-cover.png"
DEFAULT_OUTPUT = ROOT / "Agent\u6a59\u76ae\u4e66.pdf"


def browser_path() -> Path:
    candidates = [
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Chrome or Edge was not found in the usual install locations.")


def root_base_url() -> str:
    url = ROOT.resolve().as_uri()
    return url if url.endswith("/") else f"{url}/"


def cover_html(cover: Path) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Agent Orange Book Cover</title>
  <style>
    @page {{ size: A4 portrait; margin: 0; }}
    * {{ box-sizing: border-box; }}
    html, body {{
      width: 210mm;
      height: 297mm;
      margin: 0;
      background: #fff8ef;
    }}
    body {{
      display: grid;
      place-items: center;
      overflow: hidden;
    }}
    img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }}
  </style>
</head>
<body>
  <img src="{cover.resolve().as_uri()}" alt="Agent Orange Book Cover">
</body>
</html>
"""


def body_html(markdown: str) -> str:
    rendered, _, _ = render_markdown(markdown)
    rendered = rendered.replace(' loading="lazy"', "")
    meta = metadata_from_markdown(markdown)
    title = html.escape(meta["title"])
    description = html.escape(meta["description"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <base href="{root_base_url()}">
  <style>
    @page {{
      size: A4 portrait;
      margin: 15mm 15mm 17mm;
    }}

    * {{ box-sizing: border-box; }}

    html, body {{
      margin: 0;
      padding: 0;
      background: #fff;
      color: #171411;
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif;
      line-height: 1.72;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    .pdf-meta {{
      margin: 0 0 12mm;
      padding-bottom: 5mm;
      border-bottom: 1px solid #e5ded5;
      color: #5b554d;
      font-size: 10.5pt;
    }}

    .pdf-meta strong {{
      color: #f2660a;
      font-weight: 800;
    }}

    h1, h2, h3, h4, h5, h6 {{
      color: #171411;
      line-height: 1.32;
      break-after: avoid;
    }}

    h1 {{
      margin: 0 0 8mm;
      font-size: 28pt;
      letter-spacing: 0;
    }}

    h2 {{
      margin: 12mm 0 4mm;
      padding-left: 4mm;
      border-left: 4px solid #f2660a;
      font-size: 18pt;
    }}

    h3 {{
      margin: 8mm 0 3mm;
      color: #c64e00;
      font-size: 14pt;
    }}

    h4 {{
      margin: 6mm 0 2mm;
      font-size: 12pt;
    }}

    p, li {{
      color: #302b25;
      font-size: 10.5pt;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}

    p {{
      margin: 0 0 3.5mm;
    }}

    ul, ol {{
      margin: 0 0 5mm;
      padding-left: 7mm;
    }}

    li + li {{
      margin-top: 1.5mm;
    }}

    blockquote {{
      margin: 5mm 0;
      padding: 4mm 5mm;
      background: #fff7ef;
      border-left: 4px solid #f2660a;
      border-radius: 0 3mm 3mm 0;
      break-inside: avoid;
    }}

    blockquote p {{
      margin: 0;
      color: #5b554d;
    }}

    .table-scroll {{
      width: 100%;
      margin: 5mm 0 7mm;
      overflow: visible;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 9.2pt;
      break-inside: avoid;
    }}

    th, td {{
      padding: 2.6mm 3mm;
      border: 1px solid #e5ded5;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}

    th {{
      background: #f6efe7;
      color: #171411;
      font-weight: 800;
    }}

    code {{
      padding: 0.4mm 1.2mm;
      background: #f1ede8;
      border-radius: 1.2mm;
      font-family: Consolas, "Liberation Mono", monospace;
      font-size: 0.92em;
    }}

    pre {{
      max-width: 100%;
      margin: 5mm 0 6mm;
      padding: 4mm;
      overflow: hidden;
      background: #201b17;
      border-radius: 2mm;
      white-space: pre-wrap;
      break-inside: avoid;
    }}

    pre code {{
      display: block;
      padding: 0;
      background: transparent;
      color: #f7efe7;
      font-size: 8.5pt;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}

    a {{
      color: #c64e00;
      font-weight: 650;
      text-decoration-color: rgba(198, 78, 0, 0.35);
      text-underline-offset: 2px;
    }}

    figure {{
      margin: 7mm 0;
      break-inside: avoid;
    }}

    img {{
      max-width: 100%;
      height: auto;
      border: 1px solid #e5ded5;
      border-radius: 2mm;
      display: block;
    }}

    figcaption {{
      margin-top: 2mm;
      color: #8a8177;
      font-size: 8.5pt;
      line-height: 1.55;
    }}

    hr {{
      margin: 9mm 0;
      border: 0;
      border-top: 1px solid #e5ded5;
    }}
  </style>
</head>
<body>
  <main>
    <div class="pdf-meta"><strong>Agent 橙皮书</strong> · {description}</div>
{rendered}
  </main>
</body>
</html>
"""


def print_pdf(browser: Path, source_html: Path, output_pdf: Path, user_data_dir: Path) -> None:
    command = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--allow-file-access-from-files",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--user-data-dir={user_data_dir}",
        "--print-to-pdf-no-header",
        f"--print-to-pdf={output_pdf}",
        source_html.resolve().as_uri(),
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def merge_pdfs(parts: list[Path], output_pdf: Path) -> None:
    writer = PdfWriter()
    for part in parts:
        reader = PdfReader(str(part))
        for page in reader.pages:
            writer.add_page(page)
    with output_pdf.open("wb") as handle:
        writer.write(handle)


def build_pdf(markdown_path: Path, cover_path: Path, output_pdf: Path) -> None:
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown source not found: {markdown_path}")
    if not cover_path.exists():
        raise FileNotFoundError(f"Cover image not found: {cover_path}")

    markdown = markdown_path.read_text(encoding="utf-8-sig")
    browser = browser_path()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="agent-orange-book-pdf-") as tmp:
        tmp_path = Path(tmp)
        cover_page = tmp_path / "cover.html"
        body_page = tmp_path / "body.html"
        cover_pdf = tmp_path / "cover.pdf"
        body_pdf = tmp_path / "body.pdf"
        chrome_profile = tmp_path / "chrome-profile"

        cover_page.write_text(cover_html(cover_path), encoding="utf-8", newline="\n")
        body_page.write_text(body_html(markdown), encoding="utf-8", newline="\n")

        print_pdf(browser, cover_page, cover_pdf, chrome_profile)
        print_pdf(browser, body_page, body_pdf, chrome_profile)
        merge_pdfs([cover_pdf, body_pdf], output_pdf)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Agent orange book PDF.")
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--cover", type=Path, default=DEFAULT_COVER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_pdf(args.markdown, args.cover, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
