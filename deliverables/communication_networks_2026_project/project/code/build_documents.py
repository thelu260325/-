"""Generate the English report from its template and computed result tables.
Requires pandoc and XeLaTeX for document export; not required for simulations.
"""
from pathlib import Path
import csv,subprocess,os
from docx import Document
from docx.shared import Pt,Inches,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'documents'
os.environ.setdefault('XDG_CACHE_HOME','/tmp/communication-networks-cache')
def read(name):
 with (ROOT/'results'/name).open() as f:return list(csv.DictReader(f))
def table(headers,rows):
 return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(r)+' |' for r in rows)
mm=[]
for r in read('mm1_summary.csv'):
 if float(r['arrival_rate']) in [5,10,20,30,35,40,45]:
  mm.append([f"{float(r['arrival_rate']):g}",f"{1000*float(r['theory_Ws']):.2f}",f"{1000*float(r['Ws']):.2f} ± {1000*float(r['Ws_ci95_half']):.2f}",f"{100*float(r['relative_error']):+.3f}%"])
chain=[]
for r in read('integrated_summary.csv'):
 if float(r['arrival_rate']) in [5,20,25,30,40,45]:
  chain.append([f"{float(r['arrival_rate']):g}",f"{1000*float(r['poll_wait']):.2f}",f"{1000*float(r['mec_time']):.2f}",f"{1000*float(r['end_to_end']):.2f} ± {1000*float(r['end_to_end_ci95_half']):.2f}"])
opt=[]
for r in read('optimization_summary.csv'):
 opt.append([r['design'],f"{float(r['bandwidth_hz'])/1e6:g} / {float(r['mec_rate']):g}",f"{1000*float(r['mean_s']):.2f} ± {1000*float(r['mean_s_ci95_half']):.2f}",f"{100*float(r['miss_fraction']):.2f}%"])
s=(D/'report_template.md').read_text()
s=s.replace('@MM1_TABLE@',table(['λ (images/s)','Theory (ms)','Simulation ± 95% CI (ms)','Relative error'],mm))
s=s.replace('@CHAIN_TABLE@',table(['λ (images/s)','Polling wait (ms)','MEC time (ms)','End-to-end ± 95% CI (ms)'],chain))
s=s.replace('@OPT_TABLE@',table(['Design','MHz / MEC images/s','Mean total ± 95% CI (ms)','Over 100 ms'],opt))
(D/'Communication_Networks_Report.md').write_text(s)
ref=Document();sec=ref.sections[0];sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
sec.top_margin=sec.bottom_margin=Inches(.8);sec.left_margin=sec.right_margin=Inches(.85)
normal=ref.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(11)
normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.10
for name in ['Title','Heading 1','Heading 2','Heading 3']:
 ref.styles[name].font.name='Calibri';ref.styles[name].font.color.rgb=RGBColor.from_string('17324D')
ref.save(D/'reference.docx')
subprocess.run(['pandoc','Communication_Networks_Report.md','--toc','--toc-depth=2','--reference-doc=reference.docx','-o','Communication_Networks_Report.docx'],cwd=D,check=True)
doc=Document(D/'Communication_Networks_Report.docx')
cover=Document()
p=cover.add_paragraph('COMMUNICATION NETWORKS',style='Subtitle');p.paragraph_format.space_before=Inches(.9)
cover.add_heading('End-to-End Performance Modelling and Analysis',0)
cover.add_paragraph('AI-Based Quality Inspection in a 5G Smart Factory',style='Subtitle')
cover.add_paragraph('Continuous Assessment 1 • 2026–2027\nHigher Certificate & B Eng in Electronics, Year 1\nSETU (Waterford)')
t=cover.add_table(rows=1,cols=2);t.style='Table Grid';t.rows[0].cells[0].text='Team member';t.rows[0].cells[1].text='Student ID'
for name,sid in [('Sun Jiangeng','202612491511'),('Qian Tu','202612491508'),('Lu Zipeng','202612491522')]:
 cells=t.add_row().cells;cells[0].text=name;cells[1].text=sid
cover.add_paragraph('Lecturers: Yaqin Xie and Yu Zhang\nSubmission deadline: 21 November 2026\nPrepared: 9 November 2026')
cover.add_paragraph('Modelling report • Reproducible Python simulations • Team presentation')
cover.add_page_break()
for e in reversed(list(cover.element.body)[:-1]):doc.element.body.insert(0,e)
for p in doc.paragraphs:
 if p.text=='1. Executive summary':p.paragraph_format.page_break_before=True
# Cache a real, clickable contents list; Word can regenerate page numbers.
for toc in doc.element.body.findall(qn('w:sdt')):
 content=toc.find(qn('w:sdtContent'))
 if content is None: continue
 for child in list(content)[1:]:content.remove(child)
 p0=OxmlElement('w:p');r=OxmlElement('w:r')
 start=OxmlElement('w:fldChar');start.set(qn('w:fldCharType'),'begin');r.append(start)
 instr=OxmlElement('w:instrText');instr.text='TOC \\o "1-2" \\h \\z \\u';r.append(instr)
 sep=OxmlElement('w:fldChar');sep.set(qn('w:fldCharType'),'separate');r.append(sep);p0.append(r);content.append(p0)
 for hp in doc.paragraphs:
  if hp.style.name not in ['Heading 1','Heading 2']: continue
  entry=OxmlElement('w:p');pr=OxmlElement('w:pPr');st=OxmlElement('w:pStyle');st.set(qn('w:val'),'TOC1' if hp.style.name=='Heading 1' else 'TOC2');pr.append(st)
  spacing=OxmlElement('w:spacing');spacing.set(qn('w:after'),'20');pr.append(spacing);entry.append(pr)
  link=OxmlElement('w:hyperlink');bm=hp._p.find(qn('w:bookmarkStart'))
  if bm is not None:link.set(qn('w:anchor'),bm.get(qn('w:name')))
  rr=OxmlElement('w:r');tt=OxmlElement('w:t');tt.text=hp.text;rr.append(tt);link.append(rr);entry.append(link);content.append(entry)
 endp=OxmlElement('w:p');rr=OxmlElement('w:r');end=OxmlElement('w:fldChar');end.set(qn('w:fldCharType'),'end');rr.append(end);endp.append(rr);content.append(endp)
for table_ in doc.tables:
 for i,row in enumerate(table_.rows):
  for cell in row.cells:
   for p in cell.paragraphs:
    for r in p.runs:r.font.size=Pt(9)
  if i==0:
   repeat=OxmlElement('w:tblHeader');row._tr.get_or_add_trPr().append(repeat)
   for cell in row.cells:
    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EAF1F6');cell._tc.get_or_add_tcPr().append(shade)
for section in doc.sections:
 footer=section.footer.paragraphs[0];footer.alignment=2
 footer.add_run('Communication Networks  |  ')
 f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');footer._p.append(f)
settings=doc.settings.element;update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');settings.append(update)
doc.save(D/'Communication_Networks_Report.docx')
subprocess.run(['pandoc','Communication_Networks_Report.md','--toc','--toc-depth=2','--template=report_latex_template.tex',
 '--include-before-body=cover.tex','--include-in-header=header.tex','--pdf-engine=xelatex',
 '-V','documentclass=article','-V','fontsize=11pt','-V','papersize=a4','-V','geometry:margin=22mm',
 '-V','mainfont=Liberation Serif','-V','sansfont=Liberation Sans','-V','monofont=DejaVu Sans Mono',
 '-V','colorlinks=true','-V','linkcolor=blue','-V','urlcolor=blue',
 '-o','Communication_Networks_Report.pdf'],cwd=D,check=True)
print('Built report Markdown, Word and PDF.')
