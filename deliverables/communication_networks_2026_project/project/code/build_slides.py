"""Build the reviewed editable presentation and export its actual PPTX to PDF.

Requires python-pptx, reportlab (font metrics), Pillow, Matplotlib and soffice.
The PDF is an actual Impress export, rather than a separately drawn preview.
"""
from pathlib import Path
import csv,json,re,math,shutil,subprocess,tempfile,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/cn-review-mpl')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/cn-review-cache')
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.oxml.xmlchemy import OxmlElement
from PIL import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'slides';OUT.mkdir(exist_ok=True)
FONT='/usr/share/fonts/truetype/liberation/'
pdfmetrics.registerFont(TTFont('ArialLike',FONT+'LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('ArialLikeBold',FONT+'LiberationSans-Bold.ttf'))
NAVY='17324D';TEAL='087F8C';GOLD='D58A1F';GRAY='65758B';RED='BD4B46';WHITE='FFFFFF';PALE='EDF3F6'
W,H=960,540
prs=Presentation();prs.slide_width=Pt(W);prs.slide_height=Pt(H)
notes=[];layout_checks=[]
C=json.loads((ROOT/'results/configuration.json').read_text())

def read_csv(name):
 with (ROOT/'results'/name).open() as f:return list(csv.DictReader(f))

# Readable figures specifically sized for projection; report plots stay separate.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False})
for which in ['mm1','integrated']:
 rows=read_csv(which+'_summary.csv');field='Ws' if which=='mm1' else 'end_to_end'
 x=np.array([float(r['arrival_rate']) for r in rows]);y=np.array([float(r[field])*1000 for r in rows]);e=np.array([float(r[field+'_ci95_half'])*1000 for r in rows])
 fig,ax=plt.subplots(figsize=(8.2,4.3))
 if which=='mm1':
  xx=np.linspace(0,46,300);ax.plot(xx,1000/(50-xx),color='#'+TEAL,lw=2.4,label='M/M/1 theory')
 ax.errorbar(x,y,yerr=e,fmt='o-' if which=='integrated' else 'o',lw=2,color='#'+NAVY,capsize=4,label='Mean ± 95% CI')
 ax.axhline(100,color='#'+RED,ls='--',lw=1.5,label='100 ms mean limit')
 ax.set(xlabel='Total arrival rate λ (images/s)',ylabel='Mean time (ms)',xlim=(0,46),ylim=(0,310 if which=='integrated' else 225))
 ax.legend(loc='upper left',fontsize=13);ax.grid(alpha=.15);fig.tight_layout()
 fig.savefig(ROOT/'figures'/f'slide_{which}.png',dpi=200);plt.close(fig)

def shape(kind,x,y,w,h,fill):
 sh=slide.shapes.add_shape(kind,Pt(x),Pt(y),Pt(w),Pt(h));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(fill);sh.line.fill.background()
 effect=OxmlElement('a:effectLst');sh._element.spPr.append(effect)
 return sh

def rect(x,y,w,h,fill):return shape(MSO_SHAPE.RECTANGLE,x,y,w,h,fill)

def line(x0,y0,x1,y1,color=TEAL,width=2,arrow=False):
 sh=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Pt(x0),Pt(y0),Pt(x1),Pt(y1));sh.line.color.rgb=RGBColor.from_string(color);sh.line.width=Pt(width)
 if arrow:
  tail=OxmlElement('a:tailEnd');tail.set('type','triangle');sh._element.spPr.get_or_add_ln().append(tail)
 return sh

def lines_for(content,width,size,bold=False):
 font='ArialLikeBold' if bold else 'ArialLike';out=[]
 for paragraph in content.split('\n'):
  words=paragraph.split();current=''
  for word in words:
   trial=(current+' '+word).strip()
   if pdfmetrics.stringWidth(trial,font,size)>width and current:out.append(current);current=word
   else:current=trial
  out.append(current)
 return out

def text(x,y,w,h,content,size=20,color=NAVY,bold=False):
 lines=lines_for(content,w,size,bold);leading=size*1.22
 if len(lines)*leading>h+1:raise ValueError(f'Slide {len(prs.slides)} text overflow: {content[:70]}')
 tb=slide.shapes.add_textbox(Pt(x),Pt(y),Pt(w),Pt(h));tf=tb.text_frame;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.word_wrap=False
 for i,value in enumerate(lines):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=value;p.font.name='Arial';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color);p.space_before=p.space_after=Pt(0);p.line_spacing=Pt(leading)
 layout_checks.append(dict(slide=len(prs.slides),text=content,lines=len(lines),height=h,required_height=len(lines)*leading))
 return tb

def picture(name,x,y,w,h):
 path=ROOT/'figures'/name
 with Image.open(path) as im:ratio=im.width/im.height
 nw=min(w,h*ratio);nh=nw/ratio
 slide.shapes.add_picture(str(path),Pt(x+(w-nw)/2),Pt(y+(h-nh)/2),width=Pt(nw),height=Pt(nh))

def new(title,tag,speaker,seconds,script,dark=False):
 global slide
 slide=prs.slides.add_slide(prs.slide_layouts[6]);rect(0,0,W,H,NAVY if dark else WHITE);rect(0,0,12,H,TEAL)
 text(42,22,875,20,tag.upper(),11,'75D1D4' if dark else TEAL,True)
 text(42,54,876,78,title,30,WHITE if dark else NAVY,True)
 text(42,510,780,18,'Communication Networks | 2026–2027',10,'A7B8C9' if dark else GRAY)
 text(895,508,40,18,f'{len(prs.slides):02d}',11,'A7B8C9' if dark else GRAY)
 slide.notes_slide.notes_text_frame.text=f'{speaker} — {seconds} seconds\n\n{script}'
 notes.append(dict(slide=len(prs.slides),title=title,speaker=speaker,seconds=seconds,script=script))

def card(x,y,w,h,number,label,color=TEAL):
 rect(x,y,w,h,PALE);text(x+18,y+14,w-36,50,number,30,color,True);text(x+18,y+72,w-36,h-78,label,18)

def node(x,y,w,h,label):
 rect(x,y,w,h,NAVY);text(x+12,y+10,w-24,h-12,label,20,WHITE,True)

new('End-to-End Performance\nModelling and Analysis','5G smart factory · AI-based quality inspection','Sun Jiangeng',25,
"Hello everyone. We are Sun Jiangeng, Qian Tu and Lu Zipeng. Our project follows product images from industrial cameras to an edge server for AI quality inspection. We ask how routing, wireless scheduling and server queues affect delivery time, and which upgrades can help when traffic increases.",True)
text(44,176,820,70,'Communication Networks • Continuous Assessment 1\n2026–2027',20,WHITE)
text(44,282,840,108,'Sun Jiangeng  |  202612491511\nQian Tu  |  202612491508\nLu Zipeng  |  202612491522',19,WHITE)
text(44,440,820,30,'Declared assumptions • Reproducible simulations • Measured uncertainty',18,'A7B8C9')

new('Three tasks, one image journey','Project scope','Sun Jiangeng',30,
"The project has three connected tasks. We use graph theory to describe the network and select a route. We then use Shannon's formula and a polling schedule to calculate wireless delay. Finally, we use queueing theory to analyse the edge server. Python simulations test these calculations and connect the stages into a complete image journey.")
for x,n,label in [(42,'01','Graph theory\nTopology and routing'),(340,'02','Wireless access\nRate and polling delay'),(638,'03','Queueing theory\nM/M/1 and delay limits')]:card(x,168,278,210,n,label)
text(44,416,855,65,'End-to-end time = polling wait + grant + transmission\n+ backhaul + MEC waiting and processing.',21)

new('The numerical inputs are explicit assumptions','Baseline configuration','Sun Jiangeng',40,
"The brief gives no numerical parameters, so we clearly label ours as assumptions. We use four cameras, one-megabit images, twenty megahertz of bandwidth and a ten-decibel signal-to-noise ratio. The MEC, or multi-access edge computing server, processes fifty images per second on average. Our chosen mean-delay target is one hundred milliseconds. Lambda always means the total arrival rate across all four cameras, divided equally between them.")
for x,y,n,label in [(42,150,'4 cameras','Independent Poisson arrivals'),(342,150,'1 Mbit','Fixed-size baseline images'),(642,150,'20 MHz','Bandwidth; SNR = 10 dB'),(42,308,'50 images/s','Mean MEC service rate'),(342,308,'100 ms','Chosen mean-time target'),(642,308,'0.20 ms','Overhead per radio visit')]:card(x,y,276,141,n,label)
text(45,469,855,24,'λ = total images/s across four cameras; each camera generates λ/4.',18,TEAL,True)

new('A graph describes the available paths','Task 1 · topology and link attributes','Sun Jiangeng',55,
"The graph contains cameras, small base stations and the MEC server. Directed links carry capacities and propagation delays. Base station A can reach the server directly, or relay through base station B. The direct link has lower capacity than the two relay links. In this single-cell example, wireless images leave at least fourteen point six five milliseconds apart, while each relay link needs only one millisecond to transmit an image. Therefore these backhaul links do not queue. The wireless rate is available only to the camera currently scheduled.")
for i,y in enumerate([156,222,288,354],1):node(48,y,82,43,f'C{i}');line(132,y+21,310,279,TEAL,1.7,True)
node(315,254,114,48,'SBS A');node(558,154,114,48,'SBS B');node(799,254,116,48,'MEC')
line(430,267,555,187,TEAL,2.6,True);line(673,187,797,267,TEAL,2.6,True);line(430,296,796,296,GRAY,1.5,True)
text(150,145,176,70,'Wireless uplink\n69.19 Mbit/s\nwhen scheduled',17,TEAL)
text(409,166,133,62,'1 Gbit/s\n0.20 ms',18)
text(711,166,140,62,'1 Gbit/s\n0.50 ms',18)
text(498,316,275,52,'Direct: 100 Mbit/s\nPropagation: 1.00 ms',18,GRAY)
text(791,370,140,70,'FCFS server\nμ = 50/s',18)
text(45,444,730,48,'Camera nodes: λ/4 and image size.\nEdge weights: payload serialization + propagation.',18)

new('A faster route can have an extra hop','Task 1 · Dijkstra route selection','Sun Jiangeng',50,
"Dijkstra's algorithm minimises the sum of nonnegative link delays: image size divided by link capacity, plus propagation. The direct wired backhaul takes eleven milliseconds per image. The two-hop backhaul takes two point seven milliseconds. Including the common wireless payload gives a selected route weight of seventeen point one five milliseconds. That weight excludes the grant, polling wait and MEC processing, which we add separately. The relay saves eight point three milliseconds. Qian will now explain when a camera can transmit and how long its wireless stage takes.")
card(42,166,420,155,'11.00 ms','Direct wired backhaul: A → MEC',GRAY)
card(490,166,426,155,'2.70 ms','Selected wired backhaul: A → B → MEC')
text(45,359,860,70,'Selected route: C1 → A → B → MEC\nPayload + propagation: 17.15 ms; saving: 8.30 ms',23,TEAL,True)
text(45,455,855,42,'Route weight excludes the grant, polling wait and MEC processing.',17,GRAY)

new('Shannon gives an ideal scheduled rate','Task 2 · transmission time','Qian Tu',40,
"Shannon's rate is bandwidth multiplied by the base-two logarithm of one plus the linear signal-to-noise ratio. Ten decibels converts to a linear value of ten. Our scheduled rate is sixty-nine point one nine megabits per second, so a one-megabit image needs fourteen point four five milliseconds. We assign all OFDMA resource blocks to one camera per visit, reusing them in time. This is a simplified scheduling case with an ideal radio rate.")
text(45,156,855,58,'R = W log₂(1 + γ)',34,TEAL,True)
text(45,219,855,36,'SNR = 10 dB → γ = 10; W = 20 MHz',22)
card(42,285,420,145,'69.19 Mbit/s','Ideal rate while scheduled')
card(490,285,426,145,'14.45 ms','Payload duration τ = S/R')
text(45,457,855,32,'OFDMA RBs are granted to one camera at a time in this model.',18)

new('Random arrival phase creates polling wait','Task 2 · reserved one-image visits','Qian Tu',45,
"The base station visits cameras one to four in a fixed cycle. Each visit includes overhead and at most one image. Empty visits remain reserved. One cycle lasts fifty-eight point six one milliseconds. For an isolated image arriving at a random phase, the mean wait is half a cycle. Adding its grant and payload gives forty-three point nine six milliseconds. This reference assumes no older image at that camera. It is different from a simultaneous batch arriving at the cycle boundary.")
slot=95;colors=[TEAL,NAVY,GOLD,GRAY]
for i in range(8):
 x=65+i*slot;rect(x,235,slot-2,52,colors[i%4]);text(x+30,246,65,30,f'C{i%4+1}',21,WHITE,True)
line(180,194,444,194,RED,2,True);text(190,155,330,30,'Wait until the next C1 visit',20,RED)
line(180,328,180,290,RED,2,True);text(68,339,310,28,'Tagged C1 image arrives',19,RED)
line(65,391,445,391,GRAY,2);line(65,385,65,398,GRAY,2);line(445,385,445,398,GRAY,2)
text(98,400,400,28,'One cycle C = 58.61 ms',21)
text(530,334,360,70,'Each slot: g + τ = 14.65 ms\ng = 0.20 ms; τ = 14.45 ms',19)
text(45,457,860,35,'Mean tagged wireless time = C/2 + g + τ = 43.96 ms',23,TEAL,True)

new('Backlog increases the camera waiting time','Task 2 · loaded polling','Qian Tu',40,
"When older images are waiting, a new image may wait through several visits. For our reserved one-image rule, the mean polling wait is C divided by two times the quantity one minus r. Here r is the utilisation of one camera's reserved visits. At a total arrival rate of twenty-five images per second, the wait is forty-six point two five milliseconds. This wait excludes the image's own grant and payload.")
text(45,159,860,58,'Mean polling wait = C / [2(1 − r)]',31,TEAL,True)
text(45,226,860,64,'r = (λ/N)C = λ(g + τ)\nRadio stability: r < 1, or λ < 68.24 images/s',21)
card(42,333,420,140,'46.25 ms','Polling wait at total λ = 25/s')
card(490,333,426,140,'70.81 ms','Polling wait at total λ = 40/s')

new('Image-size variability changes transmission service','Further investigation required by the brief','Qian Tu',40,
"The brief also asks about random image size. If size X is exponential with mean S and transmission rate R is constant, duration X divided by R is exponential too. With Poisson input and a continuously available transmitter, that supports M/M/1. Fixed-size images instead give deterministic transmission service, supporting M/D/1 under those same conditions. Our cyclic polling and fixed overhead require separate treatment. MEC processing times are a different modelling assumption.")
text(45,149,870,32,'X = image size in bits; S = E[X]; V = X/R is transmission time.',18)
rect(42,202,420,210,PALE);rect(490,202,426,210,PALE)
text(62,222,380,35,'Fixed image size',24,TEAL,True)
text(62,278,380,109,'X = S\nV = S/R is constant\nTransmission queue: M/D/1',23)
text(510,222,386,35,'Exponential image size',24,TEAL,True)
text(510,278,386,109,'X ~ Exp(rate 1/S)\nV ~ Exp(rate R/S)\nTransmission queue: M/M/1',22)
text(45,438,865,52,'Queue labels assume Poisson input and a continuously available server.\nFixed overhead and cyclic polling modify that simple model.',18,GRAY)

new('Simulation tests each stage and the whole chain','Validation method','Qian Tu',35,
"We simulate both the isolated M/M/1 server and the actual polled chain. Each arrival-rate experiment uses thirty independent runs, with one hundred thousand measured images after a twenty-thousand-image warm-up. Confidence intervals use run averages because successive image delays are correlated. Ten deterministic tests pass, including the lecture example. We also check that the measured delay components add up. Lu will now explain the server bound and final results.")
for x,n,label in [(42,'30','Independent runs per arrival rate'),(340,'100,000','Measured images in each run'),(638,'20,000','Warm-up images discarded')]:card(x,164,278,196,n,label)
text(45,407,850,75,'11 arrival rates • Fixed seed • Pointwise 95% intervals\n10 deterministic tests passed; replication summaries included.',21)

new('Little’s law gives the M/M/1 delay bound','Task 3 · isolated Poisson-input MEC','Lu Zipeng',55,
"Here we analyse the required isolated server: Poisson arrivals, independent exponential processing and one server. State k counts waiting images plus the image being processed. Arrivals increase the state at rate lambda; departures reduce it at rate mu. Stability requires lambda below mu. Little's law connects the average number of images to their arrival rate and mean time. It gives T equal to one divided by the difference between mu and lambda. T includes waiting and processing. With mu equal to fifty and a one-hundred-millisecond limit, the maximum arrival rate is forty images per second.")
for i in range(5):
 x=106+i*151;shape(MSO_SHAPE.OVAL,x,195,48,48,NAVY);text(x+17,203,30,31,str(i),24,WHITE,True)
 if i<4:
  line(x+49,203,x+149,203,TEAL,2,True);line(x+149,235,x+49,235,GOLD,2,True)
  text(x+90,168,30,29,'λ',22,TEAL);text(x+90,245,30,29,'μ',22,GOLD)
line(759,203,840,203,TEAL,2,True);line(840,235,759,235,GOLD,2,True)
text(790,168,30,29,'λ',22,TEAL);text(790,245,30,29,'μ',22,GOLD)
text(860,205,50,45,'…',27)
text(45,299,865,34,'Ls = ρ/(1 − ρ) = λT      |      ρ = λ/μ < 1',22)
text(45,351,865,43,'T = waiting + processing = 1/(μ − λ)',28,TEAL,True)
text(45,410,865,37,'λmax = μ − 1/Tmax = 40 images/s',27,TEAL,True)
text(45,465,865,26,'μ = 50/s; Tmax = 0.100 s. A positive bound requires Tmax > 1/μ.',17,GRAY)

new('The isolated server follows the theoretical curve','Task 3 · theory versus simulation','Lu Zipeng',40,
"This plot compares simulated server time with M/M/1 theory. The largest relative difference in the mean is zero point six two percent. At forty images per second, theory gives one hundred milliseconds and simulation gives ninety-nine point three eight. Ten of eleven pointwise ninety-five-percent intervals cover theory. Universal coverage is not guaranteed. As load approaches processing capacity, waiting grows sharply, so spare capacity is important for low delay.")
picture('slide_mm1.png',30,148,672,349)
text(734,174,180,47,'0.62%',33,TEAL,True)
text(734,228,180,82,'Largest relative mean-time error',20)
text(734,340,180,90,'At λ = 40/s:\nTheory: 100 ms\nSimulation: 99.38 ms',18)
text(734,450,180,45,'10/11 pointwise CIs cover theory.',15,GRAY)

new('End-to-end delay includes the upstream stages','Integrated-chain result','Lu Zipeng',40,
"The complete chain has additional waiting and transmission stages. At twenty-five images per second, mean total delay is ninety-eight point five two milliseconds. At thirty, it is one hundred twelve point four eight. Twenty-five is therefore the highest tested rate meeting the mean target; it is not an exact continuous threshold. Polling changes the server's arrival pattern, so we simulate that actual pattern instead of assuming it remains Poisson.")
picture('slide_integrated.png',30,148,672,349)
text(734,166,180,34,'25 images/s',22,TEAL,True);text(734,210,180,44,'98.52 ms',27,TEAL,True)
text(734,290,180,34,'30 images/s',22,RED,True);text(734,334,180,44,'112.48 ms',27,RED,True)
text(734,408,180,78,'25/s is the highest tested passing rate, not an exact limit.',17,GRAY)

new('Radio and processing should be upgraded together','Controlled comparison · total λ = 40 images/s','Lu Zipeng',45,
"At forty images per second, we compare four designs using the same traffic assumptions. A faster server alone and more bandwidth alone still miss the mean target. Combining forty megahertz with a server rate of seventy-five images per second reduces the mean to fifty-seven point three one milliseconds, about sixty-seven percent below baseline. The bandwidth comparison holds SNR fixed at ten decibels, so power and cost must also be considered. About nine point five percent of images still miss the deadline: a low mean is not a per-image guarantee.")
opt=read_csv('optimization_summary.csv')
for i,r in enumerate(opt):
 y=170+i*69;value=float(r['mean_s'])*1000;half=float(r['mean_s_ci95_half'])*1000;cx=264+value*2.4
 text(43,y+5,210,35,r['design'],19);rect(264,y+3,value*2.4,30,TEAL if i==3 else NAVY)
 line(cx-half*2.4,y+18,cx+half*2.4,y+18,GOLD,2);line(cx-half*2.4,y+10,cx-half*2.4,y+26,GOLD,2);line(cx+half*2.4,y+10,cx+half*2.4,y+26,GOLD,2)
 text(cx+12,y+4,230,33,f'{value:.2f} ± {half:.2f} ms',18,TEAL if i==3 else NAVY,True)
text(45,453,868,42,'Mean ± 95% CI; SNR stays at 10 dB. Combined upgrades: 9.51% exceed 100 ms.',16)

new('Design for the whole image journey','Conclusions and questions','Lu Zipeng',20,
"To conclude, link capacity matters as well as hop count. Polling and server queues both affect delay. A server-only bound cannot guarantee end-to-end performance, and mean delay must be distinguished from deadline reliability. Thank you. We welcome your questions.",True)
text(45,163,865,175,'01  Select routes using capacity and delay.\n\n02  Include camera polling and MEC queueing.\n\n03  Check mean delay and deadline reliability separately.',23,WHITE)
text(45,390,865,48,'Questions',30,'75D1D4',True)
text(45,455,850,42,'Sources: assessment brief; course Chapter 2; Shannon (1948); Dijkstra (1959); Little (1961). Full references and derivations are in the report.',12,'A7B8C9')

pptx=OUT/'Communication_Networks_Presentation.pptx';prs.save(pptx)
(ROOT/'validation/slide_layout_checks.json').write_text(json.dumps(layout_checks,indent=2))
(OUT/'slide_notes.json').write_text(json.dumps(notes,indent=2))
assert len(notes)==15 and sum(n['seconds'] for n in notes)==600
for member in ['Sun Jiangeng','Qian Tu','Lu Zipeng']:assert sum(n['seconds'] for n in notes if n['speaker']==member)==200
s=['# Ten-minute presentation script — reviewed 11 November 2026','',
'This script matches the reviewed **15-slide** presentation. Sun Jiangeng presents slides 1–5; Qian Tu 6–10; Lu Zipeng 11–15. Each member has a 200-second allocation. These are rehearsal targets, not a measured recording. Speaking pace includes time for figures, pauses and handovers.','',
'Only read the spoken paragraphs. Slide titles, speaker labels, timing tables and Q&A are not part of the timed speech.','',
'| Slide | Speaker | Allocation (seconds) | Spoken words | Words/minute within allocation |',
'| --- | --- | ---: | ---: | ---: |']
for n in notes:
 wc=len(re.findall(r"\b[\w’'-]+\b",n['script']));n['words']=wc
 s.append(f"| {n['slide']} | {n['speaker']} | {n['seconds']} | {wc} | {wc*60/n['seconds']:.0f} |")
s+=['','## Pronunciation and equation cues','',
'- MEC: say “M E C”; SBS: “S B S”; OFDMA: “O F D M A”.','- M/M/1: “M M one”; M/D/1: “M D one”.','- λ: “lambda”; μ: “mu”; ρ: “rho”.','- Mbps or Mbit/s: “megabits per second”; MHz: “megahertz”.','- Keep denominator phrases together: “one divided by the difference between mu and lambda”; “C divided by two times the quantity one minus r”.','']
for n in notes:s += [f"## Slide {n['slide']}. {n['title'].replace(chr(10),' ')}",'',f"**Speaker:** {n['speaker']} — **allocation:** {n['seconds']} seconds",'',n['script'],'']
qa=[
('Why use M/M/1 if polling changes the arrivals?', 'Task 3 explicitly requires an M/M/1 node model. We validate that isolated model, then simulate the actual scheduler-generated MEC input. We do not assert that polling preserves Poisson arrivals.'),
('Does lambda mean the rate from one camera?', 'All plotted and quoted lambda values are aggregate rates across four cameras. Each independent camera has rate lambda/4.'),
('What does T include?', 'For the isolated M/M/1 task, T is Ws: queue waiting plus processing. End-to-end time additionally includes camera polling, grant, payload transmission and backhaul.'),
('Why are 40/s and 25/s different?', '40/s is the exact isolated-MEC mean-delay bound at mu=50/s and Tmax=0.1 s. 25/s is the highest tested end-to-end point below the same mean limit; 30/s fails. We have not identified the exact continuous threshold.'),
('Why can two backhaul hops be faster?', 'Each relay link is 1 Gbit/s rather than the direct link’s 100 Mbit/s. Two 1 ms serializations plus 0.7 ms propagation give 2.7 ms, compared with 10+1=11 ms directly. The 17.15 ms route weight adds radio payload but excludes the grant and all queueing.'),
('Is the polling scheduler an OFDMA model?', 'It is a deliberately simplified scheduler on an OFDMA-capable radio: all RBs go to one camera per visit and are reused in time. General OFDMA can schedule cameras simultaneously on disjoint RB sets; that would require different bandwidth and delay calculations.'),
('Why C/2 rather than (N−1)τ/2?', 'C/2 is the residual wait of an isolated image arriving at a random continuous phase. A simultaneous batch at cycle start is different: its mean wait before a slot is (N−1)(g+τ)/2. Under load, older images add backlog and the reserved-visit mean wait becomes C/[2(1−r)].'),
('What changes when image size is exponential?', 'At constant R, size X exponential with mean S gives X/R exponential with rate R/S. A continuously available transmission server with independent Poisson input then supports M/M/1. A fixed-size baseline would give M/D/1 under those conditions. If exponential service was already assumed, the new assumption supports that same M/M/1 model. Fixed overhead or cyclic polling require separate treatment.'),
('Why fixed-size images but exponential MEC service?', 'Image transmission duration and AI processing duration belong to different stages. The baseline fixes the radio payload size while following the requested exponential-processing assumption for the MEC.'),
('Does a 100 ms mean imply all images meet 100 ms?', 'No. At the isolated-MEC boundary, the exponential system-time tail gives about 36.8% deadline misses. In the combined-upgrade chain, the measured miss fraction is 9.51%. A reliability requirement needs its own probability target.'),
('Why is there a small difference between the two baseline simulations?', 'The arrival-rate sweep gives 174.47 ms at 40/s; the separately seeded controlled resource comparison gives 174.18 ms. Their 95% intervals overlap. Both use the same baseline parameters, and the comparison percentages use the controlled baseline.'),
('What is held fixed when bandwidth doubles?', 'SNR remains 10 dB. Maintaining this SNR over twice the bandwidth may require more received power; the comparison is not a fixed-total-power experiment. Spectrum, hardware and energy costs are not quantified.'),
('Why does one point lie outside a 95% confidence interval?', 'The intervals are pointwise estimates across repeated experiments; universal coverage of eleven points is not guaranteed. Ten of eleven contain theory, and all mean relative errors are below 0.62%. Seeds were retained.'),
('What are the main modelling difficulties and limitations?', 'We had to reconcile OFDMA with a specific polling rule, separate waiting from total time, and account for non-Poisson MEC input after scheduling. Constant SNR, exponential independent processing, infinite buffers and one active cell remain simplifying assumptions. Real deployment requires measurements and finite-buffer, interference and retransmission modelling.'),
('Are the parameter values specified by the teacher?', 'No. Four cameras, the image size, SNR, processing rate and 100 ms target are declared illustrative choices. The assignment provides the modelling tasks and distributions but no numeric parameter table.')]
s+=['# Suggested answers for the question session','', 'These answers are for the Q&A after the timed presentation.','']
for q,a in qa:s += [f'**{q}** {a}','']
(ROOT/'documents/Presentation_Script_and_QA.md').write_text('\n'.join(s))
(OUT/'slide_notes.json').write_text(json.dumps(notes,indent=2))
soffice=shutil.which('soffice')
if not soffice:raise RuntimeError('PPTX and notes built. Install LibreOffice/soffice to export the actual PPTX to PDF.')
with tempfile.TemporaryDirectory(prefix='cn-office-export-') as td:
 subprocess.run([soffice,'-env:UserInstallation=file://'+td+'/profile','--headless','--convert-to','pdf','--outdir',td,str(pptx)],check=True)
 pdf=Path(td)/pptx.with_suffix('.pdf').name
 if not pdf.exists():raise RuntimeError('Office exporter produced no PDF')
 shutil.copy2(pdf,OUT/pdf.name)
print('Built 15-slide reviewed PPTX and actual office-exported PDF, with aligned speaker notes.')
print('Spoken words:',sum(n['words'] for n in notes))
print('Allocation: 600 seconds total; 200 seconds per member.')
