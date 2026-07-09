#!/usr/bin/env python3
"""Build Agent橙皮书.md into a PDF with an Agent 橙皮书 cover page."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MARKDOWN = ROOT / "Agent橙皮书.md"
DEFAULT_OUTPUT = ROOT / "Agent橙皮书.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 18 * mm
RIGHT_MARGIN = 18 * mm
TOP_MARGIN = 16 * mm
BOTTOM_MARGIN = 16 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


def register_fonts() -> tuple[str, str]:
    regular_candidates = [
        Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    bold_candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf"),
    ]

    regular_name = "AgentBookRegular"
    bold_name = "AgentBookBold"

    for candidate in regular_candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont(regular_name, str(candidate)))
            break
    else:
        regular_name = "Helvetica"

    for candidate in bold_candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont(bold_name, str(candidate)))
            break
    else:
        bold_name = regular_name

    return regular_name, bold_name


FONT_REGULAR, FONT_BOLD = register_fonts()


def styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle(
        "Body",
        fontName=FONT_REGULAR,
        fontSize=10.5,
        leading=17,
        textColor=colors.HexColor("#211b16"),
        spaceAfter=7,
        alignment=TA_LEFT,
        wordWrap="CJK",
    )
    return {
        "body": base,
        "quote": ParagraphStyle(
            "Quote",
            parent=base,
            leftIndent=8 * mm,
            rightIndent=3 * mm,
            borderColor=colors.HexColor("#f2660a"),
            borderWidth=1.2,
            borderPadding=6,
            backColor=colors.HexColor("#fff6ee"),
            textColor=colors.HexColor("#4c4138"),
            spaceBefore=4,
            spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base,
            leftIndent=7 * mm,
            firstLineIndent=-4 * mm,
            spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "Heading1",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=23,
            leading=30,
            textColor=colors.HexColor("#17110d"),
            spaceBefore=10,
            spaceAfter=12,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=17,
            leading=23,
            textColor=colors.HexColor("#c64e00"),
            spaceBefore=14,
            spaceAfter=9,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "Heading3",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=13.5,
            leading=19,
            textColor=colors.HexColor("#34251a"),
            spaceBefore=10,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h4": ParagraphStyle(
            "Heading4",
            parent=base,
            fontName=FONT_BOLD,
            fontSize=11.5,
            leading=17,
            textColor=colors.HexColor("#4a382a"),
            spaceBefore=8,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "code": ParagraphStyle(
            "Code",
            fontName="Courier",
            fontSize=8.6,
            leading=11.5,
            textColor=colors.HexColor("#f7eee4"),
            backColor=colors.HexColor("#211b16"),
            borderPadding=8,
            spaceBefore=4,
            spaceAfter=9,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle",
            fontName=FONT_BOLD,
            fontSize=44,
            leading=56,
            textColor=colors.white,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName=FONT_REGULAR,
            fontSize=16,
            leading=25,
            textColor=colors.HexColor("#fff2e5"),
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "cover_note": ParagraphStyle(
            "CoverNote",
            fontName=FONT_REGULAR,
            fontSize=10.5,
            leading=16,
            textColor=colors.HexColor("#ffe2c2"),
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
    }


STYLES = styles()


def clean_inline(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\\([.()[\]#*_`-])", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    return html.escape(text)


def image_path_from_markdown(line: str) -> str | None:
    match = re.match(r"\s*!\[[^\]]*\]\(([^)]+)\)\s*$", line)
    return match.group(1).replace("%20", " ") if match else None


def add_paragraph(story: list, lines: list[str], style: ParagraphStyle | None = None) -> None:
    if not lines:
        return
    text = " ".join(line.strip() for line in lines if line.strip())
    if text:
        story.append(Paragraph(clean_inline(text), style or STYLES["body"]))
    lines.clear()


def scaled_image(path: Path) -> Image | None:
    if not path.exists():
        return None
    image = Image(str(path))
    max_width = CONTENT_WIDTH
    max_height = 15 * cm
    scale = min(max_width / image.imageWidth, max_height / image.imageHeight, 1)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    image.hAlign = "CENTER"
    return image


def markdown_to_flowables(markdown_path: Path) -> list:
    story: list = []
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    in_code = False

    for raw_line in markdown_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), STYLES["code"], dedent=0))
                code_lines.clear()
                in_code = False
            else:
                add_paragraph(story, paragraph_lines)
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            add_paragraph(story, paragraph_lines)
            continue

        image_target = image_path_from_markdown(line)
        if image_target:
            add_paragraph(story, paragraph_lines)
            image = scaled_image(markdown_path.parent / image_target)
            if image:
                story.append(image)
                story.append(Spacer(1, 8))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            add_paragraph(story, paragraph_lines)
            level = len(heading.group(1))
            text = clean_inline(heading.group(2))
            style_key = "h1" if level == 1 else "h2" if level == 2 else "h3" if level == 3 else "h4"
            if level == 1 and story:
                story.append(PageBreak())
            story.append(Paragraph(text, STYLES[style_key]))
            if level == 1:
                story.append(HRFlowable(width="100%", color=colors.HexColor("#f2660a"), thickness=1.2, spaceAfter=8))
            continue

        if re.match(r"^\s*[-*]\s+", line):
            add_paragraph(story, paragraph_lines)
            item = re.sub(r"^\s*[-*]\s+", "", line)
            story.append(Paragraph(f"• {clean_inline(item)}", STYLES["bullet"]))
            continue

        if line.startswith(">"):
            add_paragraph(story, paragraph_lines)
            quote = line.lstrip("> ").strip()
            if quote:
                story.append(Paragraph(clean_inline(quote), STYLES["quote"]))
            continue

        if re.match(r"^\s*---+\s*$", line):
            add_paragraph(story, paragraph_lines)
            story.append(HRFlowable(width="100%", color=colors.HexColor("#e6d8ca"), thickness=0.7, spaceBefore=6, spaceAfter=8))
            continue

        paragraph_lines.append(line)

    if in_code and code_lines:
        story.append(Preformatted("\n".join(code_lines), STYLES["code"], dedent=0))
    add_paragraph(story, paragraph_lines)
    return story


def cover_flowables(title: str) -> list:
    return [
        Spacer(1, 78 * mm),
        Paragraph(title, STYLES["cover_title"]),
        Spacer(1, 8 * mm),
        Paragraph("一份给普通人的 AI Agent 入门手册", STYLES["cover_subtitle"]),
        Spacer(1, 8 * mm),
        Paragraph("从会聊天，到会指挥。", STYLES["cover_subtitle"]),
        Spacer(1, 86 * mm),
        Paragraph("非官方开源指南 · 持续更新版", STYLES["cover_note"]),
        PageBreak(),
    ]


def draw_cover(canvas, _doc) -> None:
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#f2660a"))
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#1e1712"))
    canvas.rect(0, 0, PAGE_WIDTH, 72 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor("#ffb36e"))
    canvas.setLineWidth(1.4)
    for offset in (18, 31, 44):
        canvas.line(20 * mm, (72 + offset) * mm, PAGE_WIDTH - 20 * mm, (72 + offset) * mm)
    canvas.setFillColor(colors.HexColor("#ffffff"))
    canvas.circle(PAGE_WIDTH - 34 * mm, PAGE_HEIGHT - 34 * mm, 11 * mm, fill=0, stroke=1)
    canvas.setStrokeColor(colors.HexColor("#ffd4a8"))
    canvas.setLineWidth(2.2)
    canvas.roundRect(18 * mm, 18 * mm, PAGE_WIDTH - 36 * mm, PAGE_HEIGHT - 36 * mm, 8 * mm, stroke=1, fill=0)
    canvas.restoreState()


def draw_body_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont(FONT_REGULAR, 8)
    canvas.setFillColor(colors.HexColor("#8c7b6a"))
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, 9 * mm, f"{doc.page}")
    canvas.restoreState()


def build_pdf(markdown_path: Path, output_pdf: Path, *, title: str = "Agent 橙皮书") -> None:
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=title,
        author="Vink567",
        subject="AI Agent 入门手册",
    )
    story = cover_flowables(title)
    story.extend(markdown_to_flowables(markdown_path))
    doc.build(story, onFirstPage=draw_cover, onLaterPages=draw_body_page)


def main() -> None:
    build_pdf(DEFAULT_MARKDOWN, DEFAULT_OUTPUT)
    size_mb = DEFAULT_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"Generated {DEFAULT_OUTPUT.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
