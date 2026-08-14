"""Converte a documentacao comercial (Markdown) para DOCX com identidade visual neutra.

Dependencias: pypandoc-binary e python-docx (venv).
Uso:
    /caminho/venv/bin/python _gerar_docx.py
"""

import copy
import os
from datetime import date

import pypandoc
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_DIR = os.path.dirname(BASE_DIR)
OUT_DIR = BASE_DIR

REFERENCE_DEFAULT = "/tmp/opencode/reference-default.docx"
REFERENCE_OUT = os.path.join(OUT_DIR, "reference.docx")

DOCS = [
    "01-visao-geral-produto.md",
    "02-descricao-produto-comercial.md",
    "03-publico-alvo-personas.md",
    "04-proposta-comercial-executivo.md",
]

AZUL_ESCURO = "1F4E79"
AZUL_MEDIO = "2E74B5"
CINZA_TEXTO = "404040"
CINZA_CLARO = "808080"


def _set_style(doc, name, **kw):
    st = doc.styles[name]
    if "font" in kw:
        st.font.name = kw["font"]
        st.font._element.rPr.rFonts.set(qn("w:eastAsia"), kw["font"])
    if "size" in kw:
        st.font.size = Pt(kw["size"])
    if "bold" in kw:
        st.font.bold = kw["bold"]
    if "color" in kw:
        st.font.color.rgb = RGBColor.from_string(kw["color"])
    if "italic" in kw:
        st.font.italic = kw["italic"]
    pf = st.paragraph_format
    if "space_before" in kw:
        pf.space_before = Pt(kw["space_before"])
    if "space_after" in kw:
        pf.space_after = Pt(kw["space_after"])
    if "line_spacing" in kw:
        pf.line_spacing = kw["line_spacing"]
    if "align" in kw:
        pf.alignment = kw["align"]
    return st


def _set_char_style_color(doc, name, color):
    st = doc.styles[name]
    st.font.color.rgb = RGBColor.from_string(color)


def style_reference(doc):
    for sec in doc.sections:
        sec.page_width = Cm(21.0)
        sec.page_height = Cm(29.7)
        sec.left_margin = Cm(2.5)
        sec.right_margin = Cm(2.5)
        sec.top_margin = Cm(2.2)
        sec.bottom_margin = Cm(2.2)

    _set_style(doc, "Normal", font="Calibri", size=11, color="262626",
               space_after=8, line_spacing=1.15)
    _set_style(doc, "Body Text", font="Calibri", size=11, color="262626",
               space_after=8, line_spacing=1.15)
    _set_style(doc, "First Paragraph", font="Calibri", size=11, color="262626",
               space_after=8, line_spacing=1.15)
    _set_style(doc, "Compact", font="Calibri", size=11, color="262626",
               space_after=2, line_spacing=1.1)

    _set_style(doc, "Title", font="Calibri Light", size=40, bold=True,
               color=AZUL_ESCURO, space_before=0, space_after=12)
    _set_style(doc, "Subtitle", font="Calibri Light", size=16, color=CINZA_TEXTO,
               space_before=0, space_after=18)
    _set_style(doc, "Author", font="Calibri", size=12, color=CINZA_TEXTO, space_after=2)
    _set_style(doc, "Date", font="Calibri", size=12, color=CINZA_TEXTO, space_after=2)

    _set_style(doc, "Heading 1", font="Calibri Light", size=20, bold=True,
               color=AZUL_ESCURO, space_before=26, space_after=8)
    _set_style(doc, "Heading 2", font="Calibri Light", size=16, bold=True,
               color=AZUL_ESCURO, space_before=18, space_after=6)
    _set_style(doc, "Heading 3", font="Calibri Light", size=13, bold=True,
               color=AZUL_MEDIO, space_before=14, space_after=4)
    for name in ("Heading 4", "Heading 5", "Heading 6", "Heading 7", "Heading 8", "Heading 9"):
        _set_style(doc, name, font="Calibri", size=12, bold=True, italic=True,
                   color=AZUL_MEDIO, space_before=10, space_after=4)

    _set_style(doc, "TOC Heading", font="Calibri Light", size=18, bold=True,
               color=AZUL_ESCURO, space_before=0, space_after=12)
    _set_style(doc, "Caption", font="Calibri", size=10, color=CINZA_TEXTO)
    _set_style(doc, "Block Text", font="Calibri", size=10.5, color=CINZA_TEXTO)

    for name, color in [
        ("Heading 1 Char", AZUL_ESCURO), ("Heading 2 Char", AZUL_ESCURO),
        ("Heading 3 Char", AZUL_MEDIO), ("Title Char", AZUL_ESCURO),
        ("Subtitle Char", CINZA_TEXTO),
    ]:
        _set_char_style_color(doc, name, color)

    st = doc.styles["Hyperlink"]
    st.font.color.rgb = RGBColor.from_string("0563C1")
    st.font.underline = True

    add_table_borders(doc.styles["Table"])
    add_header_footer(doc)


def add_table_borders(table_style):
    style_el = table_style.element
    tbl_pr = style_el.find(qn("w:tblPr"))
    if tbl_pr is None:
        tbl_pr = OxmlElement("w:tblPr")
        pPr = style_el.find(qn("w:pPr"))
        if pPr is not None:
            pPr.addnext(tbl_pr)
        else:
            style_el.append(tbl_pr)
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = borders.find(qn("w:" + edge))
        if el is None:
            el = OxmlElement("w:" + edge)
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "BFBFBF")


def _add_field(par, instr):
    r1 = par.add_run()
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), "begin")
    r1._element.append(fld)
    r2 = par.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = instr
    r2._element.append(it)
    r3 = par.add_run()
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    r3._element.append(fld2)


def _clear_paragraphs(container):
    for p in list(container.paragraphs):
        p._element.getparent().remove(p._element)


def add_header_footer(doc):
    sec = doc.sections[0]
    sec.different_first_page_header_footer = True

    hp = sec.header.paragraphs[0]
    hp.text = ""
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = hp.add_run("MedSystem — Documentação Comercial")
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor.from_string(CINZA_CLARO)
    pb = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "BFBFBF")
    pb.append(bottom)
    hp._element.get_or_add_pPr().append(pb)

    fp = sec.footer.paragraphs[0]
    fp.text = ""
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = fp.add_run("Página ")
    r1.font.size = Pt(9)
    r1.font.color.rgb = RGBColor.from_string(CINZA_CLARO)
    _add_field(fp, " PAGE ")
    r2 = fp.add_run(" de ")
    r2.font.size = Pt(9)
    r2.font.color.rgb = RGBColor.from_string(CINZA_CLARO)
    _add_field(fp, " NUMPAGES ")
    for r in fp.runs:
        if r.text in ("Página ", " de "):
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor.from_string(CINZA_CLARO)


def _page_break(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_break(WD_BREAK.PAGE)


def _rule_paragraph(doc, color=AZUL_ESCURO):
    p = doc.add_paragraph()
    pb = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pb.append(bottom)
    p._element.get_or_add_pPr().append(pb)
    return p


def build_cover(doc):
    for _ in range(5):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.style = doc.styles["Title"]
    p.add_run("MedSystem")
    p2 = doc.add_paragraph()
    p2.style = doc.styles["Subtitle"]
    p2.add_run("Sistema Clínico — Documentação Comercial")
    _rule_paragraph(doc)
    for _ in range(2):
        doc.add_paragraph()
    p3 = doc.add_paragraph()
    p3.style = doc.styles["Author"]
    p3.add_run("Visão geral · Descrição do produto · Público-alvo · Proposta comercial")
    p4 = doc.add_paragraph()
    p4.style = doc.styles["Date"]
    p4.add_run(f"Versão 1.0 · {date.today().year}")
    for _ in range(10):
        doc.add_paragraph()
    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p5.add_run("Documento comercial confidencial — uso exclusivo da equipe MedSystem.")
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor.from_string(CINZA_CLARO)


def add_toc(doc):
    heading = doc.add_paragraph(style="TOC Heading")
    heading.add_run("Sumário")

    sdt = OxmlElement("w:sdt")
    sdt_pr = OxmlElement("w:sdtPr")
    doc_part = OxmlElement("w:docPartObj")
    gallery = OxmlElement("w:docPartGallery")
    gallery.set(qn("w:val"), "Table of Contents")
    unique = OxmlElement("w:docPartUnique")
    doc_part.append(gallery)
    doc_part.append(unique)
    sdt_pr.append(doc_part)
    sdt.append(sdt_pr)

    content = OxmlElement("w:sdtContent")
    p = OxmlElement("w:p")
    r_begin = OxmlElement("w:r")
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), "begin")
    r_begin.append(fld)
    p.append(r_begin)
    r_instr = OxmlElement("w:r")
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = ' TOC \\o "1-3" \\h \\z \\u '
    r_instr.append(it)
    p.append(r_instr)
    r_sep = OxmlElement("w:r")
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "separate")
    r_sep.append(fld2)
    p.append(r_sep)
    r_txt = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "Clique com o botão direito e escolha “Atualizar campo” (ou pressione F9) para gerar o sumário."
    r_txt.append(t)
    p.append(r_txt)
    r_end = OxmlElement("w:r")
    fld3 = OxmlElement("w:fldChar")
    fld3.set(qn("w:fldCharType"), "end")
    r_end.append(fld3)
    p.append(r_end)
    content.append(p)
    sdt.append(content)
    doc.element.body.append(sdt)


def clear_body(doc):
    body = doc.element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def _set_first_heading(el, text):
    if el.tag != qn("w:p"):
        return False
    ppr = el.find(qn("w:pPr"))
    if ppr is None:
        return False
    pstyle = ppr.find(qn("w:pStyle"))
    if pstyle is None or pstyle.get(qn("w:val")) != "Heading1":
        return False
    for r in el.findall(qn("w:r")):
        for t in r.findall(qn("w:t")):
            t.text = text
    return True


def append_document_body(doc, src_path, page_break_before=True, first_heading=None):
    src = Document(src_path)
    if page_break_before:
        pb = doc.add_paragraph()
        pb.paragraph_format.space_after = Pt(0)
        pb.add_run().add_break(WD_BREAK.PAGE)
    body = doc.element.body
    sect = body.find(qn("w:sectPr"))
    for child in list(src.element.body):
        if child.tag == qn("w:sectPr"):
            continue
        new_el = copy.deepcopy(child)
        if first_heading is not None and _set_first_heading(new_el, first_heading):
            first_heading = None
        if sect is not None:
            sect.addprevious(new_el)
        else:
            body.append(new_el)


def convert_md_to_docx(md_file, out_file):
    pypandoc.convert_file(
        md_file,
        "docx",
        outputfile=out_file,
        extra_args=["--reference-doc=" + REFERENCE_OUT],
    )


def main():
    reference = Document(REFERENCE_DEFAULT)
    style_reference(reference)
    reference.save(REFERENCE_OUT)

    for md_name in DOCS:
        md_path = os.path.join(MD_DIR, md_name)
        out_name = md_name[:-3] + ".docx"
        out_path = os.path.join(OUT_DIR, out_name)
        convert_md_to_docx(md_path, out_path)
        print("gerado:", out_name)

    combined = Document(REFERENCE_OUT)
    clear_body(combined)
    build_cover(combined)
    _page_break(combined)
    add_toc(combined)

    SECTIONS = [
        ("01-visao-geral-produto.md", "MedSystem — Visão Geral do Produto"),
        ("02-descricao-produto-comercial.md", "MedSystem — Descrição do Produto"),
        ("03-publico-alvo-personas.md", "MedSystem — Público-alvo e Personas"),
        ("04-proposta-comercial-executivo.md", "MedSystem — Proposta Comercial Executiva"),
    ]
    for i, (md_name, heading) in enumerate(SECTIONS):
        converted = os.path.join(OUT_DIR, md_name[:-3] + ".docx")
        append_document_body(combined, converted, page_break_before=True,
                             first_heading=heading)

    combined.core_properties.title = "MedSystem — Documentação Comercial"
    combined.core_properties.subject = "Sistema Clínico"
    combined.core_properties.author = "Equipe MedSystem"
    combined.core_properties.keywords = (
        "MedSystem, sistema clínico, documentação comercial, proposta comercial"
    )
    combined.core_properties.comments = "Documento executivo consolidado."
    combined.save(os.path.join(OUT_DIR, "MedSystem-documentacao-comercial-completa.docx"))
    print("gerado: MedSystem-documentacao-comercial-completa.docx")


if __name__ == "__main__":
    main()
