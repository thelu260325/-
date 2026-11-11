"""Build the speaking script from Markdown, then export the actual Word file.

Uses an independent, simple A4 layout so report-specific styles cannot distort
speaking notes or the timing table. Run after build_slides.py.
"""
from pathlib import Path
import re
import subprocess
import tempfile
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'documents'
NAME = 'Presentation_Script_and_QA'
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(1.8)
sec.left_margin = sec.right_margin = Cm(2)
normal = doc.styles['Normal']
normal.font.name = 'Liberation Sans'
normal.font.size = Pt(11)
normal.paragraph_format.line_spacing = 1.1
normal.paragraph_format.space_after = Pt(7)
for name, size in [('Title', 18), ('Heading 1', 16), ('Heading 2', 13)]:
    st = doc.styles[name]
    st.font.name = 'Liberation Sans'
    st.font.size = Pt(size)
    st.font.color.rgb = RGBColor.from_string('17324D')
    st.paragraph_format.space_before = Pt(10)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.keep_with_next = True

def rich(paragraph, text):
    for chunk in re.split(r'(\*\*.*?\*\*)', text):
        run = paragraph.add_run(chunk[2:-2] if chunk.startswith('**') else chunk)
        run.bold = chunk.startswith('**')

blocks = (OUT / (NAME + '.md')).read_text().strip().split('\n\n')
for block in blocks:
    if block.startswith('|'):
        rows = [line.strip().strip('|').split('|') for line in block.splitlines()]
        rows = [row for row in rows if not all(re.fullmatch(r'\s*:?-+:?\s*', c) for c in row)]
        table = doc.add_table(rows=0, cols=5)
        table.style = 'Light Shading Accent 1'
        table.autofit = False
        widths = [1.2, 3.8, 4, 3, 5]
        for col, width in zip(table.columns, widths):
            col.width = Cm(width)
        for idx, row in enumerate(rows):
            cells = table.add_row().cells
            for cell, value, width in zip(cells, row, widths):
                cell.width = Cm(width)
                p = cell.paragraphs[0]
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.space_before = Pt(3)
                p.paragraph_format.line_spacing = 1
                run = p.add_run(value.strip())
                run.font.size = Pt(9)
                run.bold = idx == 0
            props = table.rows[-1]._tr.get_or_add_trPr()
            props.append(OxmlElement('w:cantSplit'))
            if idx == 0:
                props.append(OxmlElement('w:tblHeader'))
    elif block.startswith('#'):
        level = len(block) - len(block.lstrip('#'))
        title = block.lstrip('# ').replace('\n', ' ')
        p = doc.add_paragraph(style='Title' if not doc.paragraphs else f'Heading {level}')
        if title.startswith(('Slide 1.', 'Slide 6.', 'Slide 11.', 'Suggested answers')):
            p.paragraph_format.page_break_before = True
        rich(p, title)
    elif block.startswith('- '):
        for line in block.splitlines():
            rich(doc.add_paragraph(style='List Bullet'), line.removeprefix('- '))
    else:
        p = doc.add_paragraph()
        rich(p, block.replace('\n', ' '))
        p.paragraph_format.keep_together = True
        if block.startswith('**Speaker:'):
            p.paragraph_format.keep_with_next = True
            for run in p.runs:
                run.font.size = Pt(10)
                run.font.color.rgb = RGBColor.from_string('65758B')
footer = sec.footer.paragraphs[0]
footer.alignment = 2
footer.add_run('Presentation script | ')
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)
for run in footer.runs:
    run.font.size = Pt(9)
doc.save(OUT / (NAME + '.docx'))
with tempfile.TemporaryDirectory(prefix='cn-script-office-') as temp:
    subprocess.run(['soffice', f'-env:UserInstallation={Path(temp).as_uri()}',
        '--headless', '--convert-to', 'pdf', '--outdir', str(OUT),
        str(OUT / (NAME + '.docx'))], check=True)
print('Built speaking script DOCX and actual Writer PDF from shared Markdown.')
