#!/usr/bin/env python3
"""Build the Agent orange book Markdown into a static reading site."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MARKDOWN = ROOT / "Agent橙皮书.md"
DEFAULT_OUTPUT_DIR = ROOT
MARKDOWN_NAME = "Agent橙皮书.md"
PAGES_URL = "https://codex.bozhouai.com/"


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    slug: str


def clean_inline(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\\([.()[\]#*_`+\-])", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()


def slug_base(text: str) -> str:
    text = clean_inline(text).lower()
    text = re.sub(
        r"[`~!@#$%^&*()=+\[\]{}\\|;:'\"<>,./?！￥…（）【】{}、，。；：“”‘’《》？]",
        "",
        text,
    )
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "section"


def unique_slug(text: str, counts: dict[str, int]) -> str:
    base = slug_base(text)
    count = counts.get(base, 0)
    counts[base] = count + 1
    return base if count == 0 else f"{base}_{count}"


def render_inline(text: str) -> str:
    text = re.sub(r"\\([.()[\]#*_`+\-])", r"\1", text.strip())

    links: list[str] = []

    def store(value: str) -> str:
        links.append(value)
        return f"\u0000{len(links) - 1}\u0000"

    def code_repl(match: re.Match[str]) -> str:
        return store(f"<code>{html.escape(match.group(1), quote=True)}</code>")

    def link_repl(match: re.Match[str]) -> str:
        label = render_inline(match.group(1))
        href = html.escape(match.group(2), quote=True)
        return store(f'<a href="{href}">{label}</a>')

    text = re.sub(r"`([^`]+)`", code_repl, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)
    text = html.escape(text, quote=True)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)

    for index, value in enumerate(links):
        text = text.replace(f"\u0000{index}\u0000", value)
    text = text.replace("&lt;br&gt;", "<br>")
    return text


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return len(cells) > 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_table(rows: list[str]) -> str:
    header = split_table_row(rows[0])
    body = [split_table_row(row) for row in rows[2:]]
    out = ['<div class="table-scroll">', "<table>", "<thead>", "<tr>"]
    out.extend(f"<th>{render_inline(cell)}</th>" for cell in header)
    out.extend(["</tr>", "</thead>"])
    if body:
        out.append("<tbody>")
        for row in body:
            out.append("<tr>")
            out.extend(f"<td>{render_inline(cell)}</td>" for cell in row)
            out.append("</tr>")
        out.append("</tbody>")
    out.extend(["</table>", "</div>"])
    return "\n".join(out)


def render_markdown(markdown: str) -> tuple[str, list[Heading], str | None]:
    lines = markdown.splitlines()
    index = 0
    html_blocks: list[str] = []
    headings: list[Heading] = []
    slug_counts: dict[str, int] = {}
    hero_image: str | None = None

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if stripped.startswith("<!--") and stripped.endswith("-->"):
            index += 1
            continue

        code_match = re.match(r"^```([A-Za-z0-9_+\-. ]*)\s*$", stripped)
        if code_match:
            language = code_match.group(1).strip().replace(" ", "-").lower()
            index += 1
            code_lines: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            class_attr = f' class="language-{html.escape(language, quote=True)}"' if language else ""
            code = html.escape("\n".join(code_lines), quote=False)
            html_blocks.append(f"<pre><code{class_attr}>{code}</code></pre>")
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = clean_inline(heading_match.group(2))
            slug = unique_slug(text, slug_counts)
            headings.append(Heading(level=level, text=text, slug=slug))
            html_blocks.append(f'<h{level} id="{html.escape(slug, quote=True)}">{render_inline(text)}</h{level}>')
            index += 1
            continue

        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            alt = clean_inline(image_match.group(1)) or "Agent 橙皮书配图"
            src = image_match.group(2).strip()
            if hero_image is None:
                hero_image = src
            html_blocks.append(
                '<figure class="book-figure">'
                f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" loading="lazy">'
                f"<figcaption>{html.escape(alt)}</figcaption>"
                "</figure>"
            )
            index += 1
            continue

        if re.fullmatch(r"[-*_]{3,}", stripped):
            html_blocks.append("<hr>")
            index += 1
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            text = "<br>\n".join(render_inline(item) for item in quote_lines if item)
            html_blocks.append(f"<blockquote><p>{text}</p></blockquote>")
            continue

        if index + 1 < len(lines) and "|" in stripped and is_table_separator(lines[index + 1]):
            table_lines = [stripped, lines[index + 1].strip()]
            index += 2
            while index < len(lines) and "|" in lines[index].strip() and lines[index].strip():
                table_lines.append(lines[index].strip())
                index += 1
            html_blocks.append(render_table(table_lines))
            continue

        unordered = re.match(r"^\s*[-*+]\s+(.+)$", line)
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if unordered or ordered:
            tag = "ul" if unordered else "ol"
            items: list[str] = []
            pattern = r"^\s*[-*+]\s+(.+)$" if unordered else r"^\s*\d+[.)]\s+(.+)$"
            while index < len(lines):
                match = re.match(pattern, lines[index])
                if not match:
                    break
                items.append(f"<li>{render_inline(match.group(1))}</li>")
                index += 1
            html_blocks.append(f"<{tag}>\n" + "\n".join(items) + f"\n</{tag}>")
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            next_line = lines[index]
            next_stripped = next_line.strip()
            if not next_stripped:
                break
            if (
                next_stripped.startswith("#")
                or next_stripped.startswith(">")
                or next_stripped.startswith("```")
                or re.fullmatch(r"!\[[^\]]*\]\([^)]+\)", next_stripped)
                or re.fullmatch(r"[-*_]{3,}", next_stripped)
                or re.match(r"^\s*[-*+]\s+", next_line)
                or re.match(r"^\s*\d+[.)]\s+", next_line)
                or (index + 1 < len(lines) and "|" in next_stripped and is_table_separator(lines[index + 1]))
            ):
                break
            paragraph_lines.append(next_stripped)
            index += 1

        joined = "<br>\n".join(render_inline(item) for item in paragraph_lines)
        html_blocks.append(f"<p>{joined}</p>")

    return "\n".join(html_blocks), headings, hero_image


def metadata_from_markdown(markdown: str) -> dict[str, str]:
    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    checked_match = re.search(r"最后校验[^\d]*(\d{4}-\d{2}-\d{2})", markdown)
    title = clean_inline(title_match.group(1)) if title_match else "Agent 橙皮书"
    return {
        "title": title,
        "short_title": "Agent 橙皮书",
        "description": "一份给普通人的 AI Agent 入门手册，从会聊天到会指挥，帮助你理解、使用并验收 Agent。",
        "version": "持续更新版",
        "checked": checked_match.group(1) if checked_match else "2026-07-09",
        "scope": "认知 · 概念 · 使用方法 · 实战案例 · 风险进阶",
    }


def build_toc(headings: list[Heading]) -> str:
    toc_items: list[str] = []
    for heading in headings:
        if heading.level not in (2, 3) or heading.text == "目录":
            continue
        modifier = " toc-link--sub" if heading.level == 3 else ""
        toc_items.append(
            f'<a class="toc-link{modifier}" href="#{html.escape(heading.slug, quote=True)}">'
            f"{html.escape(heading.text)}</a>"
        )
    return "\n".join(toc_items)


def build_page(markdown: str, page_name: str = "index.html") -> str:
    markdown = markdown.lstrip("\ufeff")
    body_html, headings, hero_image = render_markdown(markdown)
    meta = metadata_from_markdown(markdown)
    toc_html = build_toc(headings)
    markdown_url = quote(MARKDOWN_NAME)
    hero_src = hero_image or "图片和附件/image%202.png"

    canonical = PAGES_URL if page_name == "index.html" else f"{PAGES_URL}{page_name}"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(meta["title"])}</title>
  <meta name="description" content="{html.escape(meta["description"], quote=True)}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{html.escape(meta["title"], quote=True)}">
  <meta property="og:description" content="{html.escape(meta["description"], quote=True)}">
  <meta name="theme-color" content="#f2660a">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="assets/site.css">
  <script defer src="assets/site.js"></script>
</head>
<body>
  <div class="progress" aria-hidden="true"><span></span></div>

  <header class="topbar">
    <a class="brand" href="#top" aria-label="返回顶部">
      <span class="brand-mark">A</span>
      <span>Agent 橙皮书</span>
    </a>
    <nav class="topnav" aria-label="主导航">
      <a href="#online-book">在线阅读</a>
      <a href="#toc">目录</a>
      <a href="{markdown_url}">查看 Markdown</a>
    </nav>
  </header>

  <main id="top">
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero-copy">
        <p class="eyebrow">NON-OFFICIAL GUIDE · 持续更新版</p>
        <h1 id="hero-title">{html.escape(meta["short_title"])}</h1>
        <p class="hero-lede">{html.escape(meta["description"])}</p>
        <div class="hero-actions" aria-label="主要操作">
          <a class="button button-primary" href="#online-book">开始阅读</a>
          <a class="button button-secondary" href="{markdown_url}">查看 Markdown</a>
          <a class="button button-ghost" href="#toc">浏览目录</a>
        </div>
      </div>
      <div class="hero-side">
        <img class="hero-preview" src="{html.escape(hero_src, quote=True)}" alt="Agent 橙皮书内容预览">
        <div class="hero-panel" aria-label="书籍信息">
          <div>
            <span class="panel-label">版本</span>
            <strong>{html.escape(meta["version"])}</strong>
          </div>
          <div>
            <span class="panel-label">最后校验</span>
            <strong>{html.escape(meta["checked"])}</strong>
          </div>
          <div>
            <span class="panel-label">内容范围</span>
            <strong>{html.escape(meta["scope"])}</strong>
          </div>
        </div>
      </div>
    </section>

    <section class="book-shell" id="online-book">
      <aside class="toc-panel" id="toc" aria-label="文章目录">
        <div class="toc-heading">目录</div>
        <nav class="toc-list">
{toc_html}
        </nav>
      </aside>

      <article class="book-content">
{body_html}
      </article>
    </section>
  </main>

  <button class="back-top" type="button" data-back-top aria-label="返回顶部">↑</button>
</body>
</html>
"""


def build_cover() -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent 橙皮书封面</title>
  <meta name="theme-color" content="#f2660a">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="assets/site.css">
</head>
<body class="cover-page">
  <main class="cover-stage" aria-label="Agent 橙皮书封面">
    <section class="cover-card">
      <p class="cover-kicker">NON-OFFICIAL GUIDE</p>
      <h1>Agent 橙皮书</h1>
      <p>给普通人的 AI Agent 入门与实战指南</p>
      <div class="cover-meta">
        <span>v0.1.0</span>
        <span>2026-07-09</span>
        <span>持续更新版</span>
      </div>
      <div class="cover-actions">
        <a class="button button-primary" href="index.html">在线阅读</a>
        <a class="button button-secondary" href="{quote(MARKDOWN_NAME)}">查看 Markdown</a>
      </div>
    </section>
  </main>
</body>
</html>
"""


def build_site(markdown_path: Path = DEFAULT_MARKDOWN, output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    markdown = markdown_path.read_text(encoding="utf-8-sig")
    output_dir.mkdir(parents=True, exist_ok=True)
    index_html = build_page(markdown, "index.html")
    (output_dir / "index.html").write_text(index_html, encoding="utf-8", newline="\n")
    (output_dir / "book.html").write_text(build_page(markdown, "book.html"), encoding="utf-8", newline="\n")
    (output_dir / "cover.html").write_text(build_cover(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build_site()
