#!/usr/bin/env python3
"""Generate the operational retention policy PDF from its Markdown source."""

import re
from pathlib import Path

from fpdf import FPDF


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "politica-retencao-descarte-backup.md"
OUTPUT = ROOT / "docs" / "politica-retencao-descarte-backup.pdf"

FONT_REGULAR = Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf")
FONT_BOLD = Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf")
FONT_MONO = Path("/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf")

NAVY = (25, 55, 86)
BLUE = (35, 104, 148)
LIGHT_BLUE = (231, 241, 247)
TEXT = (41, 49, 56)
MUTED = (100, 110, 120)
LIGHT_GRAY = (244, 246, 248)
GRID = (201, 210, 218)
WHITE = (255, 255, 255)


def clean_inline(text):
    text = re.sub(r"!\[([^]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("`", "").replace("~~", "")
    return text.strip()


class PolicyPDF(FPDF):
    def __init__(self, running_title="Política de Retenção, Descarte e Backup"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.running_title = running_title
        self.cover_page = True
        self.set_margins(18, 20, 18)
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font("Noto", style="", fname=str(FONT_REGULAR))
        self.add_font("Noto", style="B", fname=str(FONT_BOLD))
        self.add_font("NotoMono", style="", fname=str(FONT_MONO))
        self.alias_nb_pages()

    def header(self):
        if self.cover_page:
            return
        self.set_draw_color(*GRID)
        self.set_text_color(*MUTED)
        self.set_font("Noto", size=8)
        self.cell(0, 5, f"Sistema Clínico MVP | {self.running_title}")
        self.ln(7)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)

    def footer(self):
        if self.cover_page:
            return
        self.set_y(-13)
        self.set_draw_color(*GRID)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_text_color(*MUTED)
        self.set_font("Noto", size=8)
        self.cell(0, 5, f"Uso interno | Página {self.page_no()} de {{nb}}", align="R")

    def add_content_page(self):
        self.cover_page = False
        self.add_page()


def ensure_space(pdf, height):
    if pdf.get_y() + height > pdf.h - pdf.b_margin:
        pdf.add_page()


def wrap_text(pdf, text, width):
    paragraphs = str(text).splitlines() or [""]
    wrapped = []
    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            wrapped.append("")
            continue
        expanded_words = []
        for word in words:
            if pdf.get_string_width(word) <= width:
                expanded_words.append(word)
                continue
            chunk = ""
            for char in word:
                if chunk and pdf.get_string_width(chunk + char) > width:
                    expanded_words.append(chunk)
                    chunk = char
                else:
                    chunk += char
            if chunk:
                expanded_words.append(chunk)
        line = expanded_words[0]
        for word in expanded_words[1:]:
            candidate = f"{line} {word}"
            if pdf.get_string_width(candidate) <= width:
                line = candidate
            else:
                wrapped.append(line)
                line = word
        wrapped.append(line)
    return wrapped


def render_cover(
    pdf,
    title="Política de Retenção,\nDescarte e Backup",
    subtitle="Uso operacional e controles LGPD",
    status="Minuta técnico-operacional",
    warning=None,
):
    pdf.cover_page = True
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, 70, style="F")
    pdf.set_xy(18, 22)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Noto", "B", 24)
    pdf.multi_cell(174, 10, title)
    pdf.set_x(18)
    pdf.set_font("Noto", size=12)
    pdf.cell(0, 9, subtitle)

    pdf.set_xy(18, 92)
    pdf.set_text_color(*NAVY)
    pdf.set_font("Noto", "B", 16)
    pdf.cell(0, 8, "Sistema Clínico MVP")
    pdf.ln(16)

    metadata = (
        ("Versão", "1.0"),
        ("Emissão", "13 de agosto de 2026"),
        ("Classificação", "Uso interno"),
        ("Status", status),
    )
    for label, value in metadata:
        pdf.set_font("Noto", "B", 10)
        pdf.set_text_color(*MUTED)
        pdf.cell(38, 8, label.upper())
        pdf.set_font("Noto", size=10)
        pdf.set_text_color(*TEXT)
        pdf.cell(0, 8, value)
        pdf.ln(9)

    warning = warning or (
        "Os prazos e as automações destrutivas dependem de validação do Controlador, "
        "DPO, jurídico/regulatório e responsável assistencial. Este documento não "
        "representa declaração de conformidade plena com a LGPD."
    )
    pdf.set_y(190)
    pdf.set_fill_color(255, 246, 224)
    pdf.set_draw_color(230, 178, 80)
    pdf.rect(18, pdf.get_y(), 174, 52, style="DF")
    pdf.set_xy(24, pdf.get_y() + 7)
    pdf.set_text_color(102, 70, 18)
    pdf.set_font("Noto", "B", 10)
    pdf.cell(0, 6, "CONDIÇÃO DE VIGÊNCIA")
    pdf.ln(8)
    pdf.set_x(24)
    pdf.set_font("Noto", size=9)
    pdf.multi_cell(
        162,
        5,
        warning,
    )


def render_heading(pdf, level, text):
    sizes = {1: 18, 2: 14, 3: 11}
    before = {1: 8, 2: 6, 3: 4}
    after = {1: 4, 2: 3, 3: 2}
    ensure_space(pdf, 18)
    pdf.ln(before[level])
    pdf.set_text_color(*(NAVY if level < 3 else BLUE))
    pdf.set_font("Noto", "B", sizes[level])
    pdf.multi_cell(0, sizes[level] * 0.42, clean_inline(text))
    if level == 1:
        pdf.set_draw_color(*BLUE)
        pdf.set_line_width(0.6)
        pdf.line(pdf.l_margin, pdf.get_y() + 1, pdf.l_margin + 24, pdf.get_y() + 1)
        pdf.set_line_width(0.2)
    pdf.ln(after[level])


def render_paragraph(pdf, text, indent=0):
    text = clean_inline(text)
    if not text:
        pdf.ln(2)
        return
    pdf.set_text_color(*TEXT)
    pdf.set_font("Noto", size=9.2)
    pdf.set_x(pdf.l_margin + indent)
    pdf.multi_cell(pdf.epw - indent, 5.1, text, align="J")
    pdf.ln(1.2)


def render_bullet(pdf, text, ordered=False):
    marker, content = text.split(" ", 1)
    if content.startswith("[ ] "):
        content = "[ ] " + content[4:]
    prefix = f"{marker} " if ordered else "• "
    pdf.set_text_color(*TEXT)
    pdf.set_font("Noto", size=9.2)
    pdf.set_x(pdf.l_margin + 3)
    pdf.multi_cell(pdf.epw - 3, 5.1, prefix + clean_inline(content))
    pdf.ln(0.5)


def render_quote(pdf, lines):
    text = clean_inline(" ".join(line.lstrip("> ") for line in lines))
    pdf.set_font("Noto", size=8.8)
    wrapped = wrap_text(pdf, text, pdf.epw - 14)
    height = max(18, len(wrapped) * 4.8 + 9)
    ensure_space(pdf, height + 3)
    y = pdf.get_y()
    pdf.set_fill_color(255, 246, 224)
    pdf.set_draw_color(230, 178, 80)
    pdf.rect(pdf.l_margin, y, pdf.epw, height, style="DF")
    pdf.set_xy(pdf.l_margin + 6, y + 4)
    pdf.set_text_color(102, 70, 18)
    pdf.set_font("Noto", "B", 8.8)
    pdf.multi_cell(pdf.epw - 12, 4.8, text)
    pdf.set_y(y + height + 3)


def render_code(pdf, lines):
    pdf.set_font("NotoMono", size=7.3)
    all_lines = []
    for line in lines:
        if not line:
            all_lines.append(" ")
            continue
        indent = line[:len(line) - len(line.lstrip())]
        wrapped = wrap_text(pdf, line.lstrip(), pdf.epw - 10 - pdf.get_string_width(indent))
        all_lines.extend(
            [f"{indent}{part}" if index == 0 else f"{indent}  {part}"
             for index, part in enumerate(wrapped)]
        )
    height = len(all_lines) * 4.1 + 8
    if height > pdf.h - pdf.t_margin - pdf.b_margin - 15:
        chunks = []
        current = []
        for line in all_lines:
            current.append(line)
            if len(current) >= 42:
                chunks.append(current)
                current = []
        if current:
            chunks.append(current)
    else:
        chunks = [all_lines]

    for chunk in chunks:
        block_height = len(chunk) * 4.1 + 8
        ensure_space(pdf, block_height + 3)
        y = pdf.get_y()
        pdf.set_fill_color(*LIGHT_GRAY)
        pdf.set_draw_color(*GRID)
        pdf.rect(pdf.l_margin, y, pdf.epw, block_height, style="DF")
        pdf.set_xy(pdf.l_margin + 5, y + 4)
        pdf.set_text_color(32, 52, 67)
        pdf.set_font("NotoMono", size=7.3)
        for line in chunk:
            pdf.cell(pdf.epw - 10, 4.1, line)
            pdf.ln(4.1)
            pdf.set_x(pdf.l_margin + 5)
        pdf.set_y(y + block_height + 3)


def table_widths(columns, total):
    if columns == 2:
        return [total * 0.28, total * 0.72]
    if columns == 3:
        return [total * 0.22, total * 0.28, total * 0.50]
    if columns == 4:
        return [total * 0.22, total * 0.18, total * 0.25, total * 0.35]
    if columns == 5:
        return [total * 0.18, total * 0.12, total * 0.18, total * 0.18, total * 0.34]
    return [total / columns] * columns


def render_table(pdf, rows):
    parsed = [
        [clean_inline(cell) for cell in row.strip().strip("|").split("|")]
        for row in rows
    ]
    if len(parsed) > 1 and all(re.fullmatch(r"\s*:?-{3,}:?\s*", cell) for cell in parsed[1]):
        parsed.pop(1)
    if not parsed:
        return

    column_count = max(len(row) for row in parsed)
    widths = table_widths(column_count, pdf.epw)
    line_height = 4.1

    for row_index, row in enumerate(parsed):
        row += [""] * (column_count - len(row))
        pdf.set_font("Noto", "B" if row_index == 0 else "", 7.2)
        wrapped_cells = [
            wrap_text(pdf, value, width - 4)
            for value, width in zip(row, widths)
        ]
        row_height = max(8, max(len(lines) for lines in wrapped_cells) * line_height + 4)
        ensure_space(pdf, row_height)
        start_x = pdf.l_margin
        start_y = pdf.get_y()
        for column, (lines, width) in enumerate(zip(wrapped_cells, widths)):
            if row_index == 0:
                pdf.set_fill_color(*NAVY)
                pdf.set_text_color(*WHITE)
            elif row_index % 2:
                pdf.set_fill_color(*WHITE)
                pdf.set_text_color(*TEXT)
            else:
                pdf.set_fill_color(*LIGHT_BLUE)
                pdf.set_text_color(*TEXT)
            pdf.set_draw_color(*GRID)
            pdf.rect(start_x, start_y, width, row_height, style="DF")
            pdf.set_xy(start_x + 2, start_y + 2)
            pdf.set_font("Noto", "B" if row_index == 0 else "", 7.2)
            for line in lines:
                pdf.cell(width - 4, line_height, line)
                pdf.ln(line_height)
                pdf.set_x(start_x + 2)
            start_x += width
        pdf.set_y(start_y + row_height)
    pdf.ln(3)


def parse_blocks(lines):
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        if line.startswith("```"):
            language = line[3:].strip()
            block = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                block.append(lines[index].rstrip("\n"))
                index += 1
            yield ("code", language, block)
        elif line.startswith("|"):
            block = []
            while index < len(lines) and lines[index].rstrip().startswith("|"):
                block.append(lines[index].rstrip())
                index += 1
            index -= 1
            yield ("table", block)
        elif line.startswith(">"):
            block = []
            while index < len(lines) and lines[index].rstrip().startswith(">"):
                block.append(lines[index].rstrip())
                index += 1
            index -= 1
            yield ("quote", block)
        else:
            yield ("line", line)
        index += 1


def generate_document(source, output, *, title, cover_title, subtitle, status, warning):
    if not source.exists():
        raise SystemExit(f"Markdown source not found: {source}")
    for font in (FONT_REGULAR, FONT_BOLD, FONT_MONO):
        if not font.exists():
            raise SystemExit(f"Required font not found: {font}")

    lines = source.read_text(encoding="utf-8").splitlines()
    pdf = PolicyPDF(title)
    pdf.set_title(title)
    pdf.set_author("Sistema Clínico MVP")
    pdf.set_subject(title)
    render_cover(
        pdf,
        title=cover_title,
        subtitle=subtitle,
        status=status,
        warning=warning,
    )
    pdf.add_content_page()

    for block in parse_blocks(lines):
        kind = block[0]
        if kind == "code":
            render_code(pdf, block[2])
            continue
        if kind == "table":
            render_table(pdf, block[1])
            continue
        if kind == "quote":
            render_quote(pdf, block[1])
            continue

        line = block[1]
        if not line or line == "---":
            if not line:
                pdf.ln(1)
            continue
        if line.startswith("# "):
            # The document title and metadata are represented on the cover.
            continue
        if line.startswith("## "):
            render_heading(pdf, 1, line[3:])
        elif line.startswith("### "):
            render_heading(pdf, 2, line[4:])
        elif line.startswith("#### "):
            render_heading(pdf, 3, line[5:])
        elif re.match(r"^\d+\.\s+", line):
            render_bullet(pdf, line, ordered=True)
        elif line.startswith("- "):
            render_bullet(pdf, line)
        elif line.startswith("**Sistema:**") or line.startswith("**Versão:**"):
            continue
        elif line.startswith("**Data de emissão:**") or line.startswith("**Classificação:**"):
            continue
        elif line.startswith("**Status:**"):
            continue
        else:
            render_paragraph(pdf, line)

    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))
    print(f"PDF generated: {output}")


def generate():
    generate_document(
        SOURCE,
        OUTPUT,
        title="Política de Retenção, Descarte e Backup",
        cover_title="Política de Retenção,\nDescarte e Backup",
        subtitle="Uso operacional e controles LGPD",
        status="Minuta técnico-operacional",
        warning=None,
    )


if __name__ == "__main__":
    generate()
