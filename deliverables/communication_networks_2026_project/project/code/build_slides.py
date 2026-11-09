"""Create editable PPTX, matching PDF handout and embedded speaker notes.
The PDF is drawn from the same layout primitives; it is not an Office export.
"""
from pathlib import Path
import csv,json,re,textwrap
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'slides';OUT.mkdir(exist_ok=True)
FONT='/usr/share/fonts/truetype/liberation/'
pdfmetrics.registerFont(TTFont('ArialLike',FONT+'LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('ArialLikeBold',FONT+'LiberationSans-Bold.ttf'))
NAVY='17324D';TEAL='087F8C';GOLD='D58A1F';GRAY='65758B';RED='BD4B46';WHITE='FFFFFF';PALE='EDF3F6'
W,H=960,540
prs=Presentation();prs.slide_width=Pt(W);prs.slide_height=Pt(H)
cv=canvas.Canvas(str(OUT/'Communication_Networks_Presentation.pdf'),pagesize=(W,H))
cv.setTitle('5G Smart Factory — Communication Networks');cv.setAuthor('Sun Jiangeng; Qian Tu; Lu Zipeng')
notes=[];layout_checks=[]

def col(hex): return tuple(int(hex[i:i+2],16)/255 for i in (0,2,4))
def rect(x,y,w,h,fill):
 shape=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Pt(x),Pt(y),Pt(w),Pt(h));shape.fill.solid();shape.fill.fore_color.rgb=RGBColor.from_string(fill);shape.line.fill.background()
 cv.setFillColorRGB(*col(fill));cv.rect(x,H-y-h,w,h,stroke=0,fill=1)
def lines_for(text,width,size,bold=False):
 name='ArialLikeBold' if bold else 'ArialLike';out=[]
 for paragraph in text.split('\n'):
  words=paragraph.split();line=''
  for word in words:
   trial=(line+' '+word).strip()
   if pdfmetrics.stringWidth(trial,name,size)>width and line:out.append(line);line=word
   else:line=trial
  out.append(line)
 return out

def text(x,y,w,h,content,size=20,color=NAVY,bold=False):
 lines=lines_for(content,w,size,bold);leading=size*1.22
 if len(lines)*leading>h+1:raise ValueError(f'Slide {len(prs.slides)} text overflow: {content[:70]}')
 tb=slide.shapes.add_textbox(Pt(x),Pt(y),Pt(w),Pt(h));tf=tb.text_frame;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0;tf.word_wrap=False
 for i,line in enumerate(lines):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='Arial';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color);p.space_before=p.space_after=Pt(0);p.line_spacing=Pt(leading)
 cv.setFillColorRGB(*col(color));cv.setFont('ArialLikeBold' if bold else 'ArialLike',size)
 for i,line in enumerate(lines):cv.drawString(x,H-y-size-i*leading,line)
 layout_checks.append(dict(slide=len(prs.slides),text=content[:45],lines=len(lines),height=h,required_height=len(lines)*leading))

def picture(name,x,y,w,h):
 path=ROOT/'figures'/name
 with Image.open(path) as im:ratio=im.width/im.height
 nw=min(w,h*ratio);nh=nw/ratio;xx=x+(w-nw)/2;yy=y+(h-nh)/2
 slide.shapes.add_picture(str(path),Pt(xx),Pt(yy),width=Pt(nw),height=Pt(nh));cv.drawImage(str(path),xx,H-yy-nh,nw,nh,mask='auto')

def new(title,tag,speaker,seconds,script,dark=False):
 global slide
 if len(prs.slides):cv.showPage()
 slide=prs.slides.add_slide(prs.slide_layouts[6]);bg=NAVY if dark else WHITE
 rect(0,0,W,H,bg);rect(0,0,12,H,TEAL)
 text(42,22,875,20,tag.upper(),11,TEAL if not dark else '75D1D4',True)
 text(42,54,876,78,title,30,WHITE if dark else NAVY,True)
 text(42,510,760,18,f'Communication Networks | {speaker} | {seconds}s',10,'A7B8C9' if dark else GRAY)
 text(895,508,40,18,f'{len(prs.slides):02d}',11,'A7B8C9' if dark else GRAY)
 slide.notes_slide.notes_text_frame.text=f'{speaker} — {seconds} seconds\n\n{script}'
 notes.append(dict(slide=len(prs.slides),title=title,speaker=speaker,seconds=seconds,script=script))

def card(x,y,w,h,number,label,color=TEAL):
 rect(x,y,w,h,PALE);text(x+18,y+14,w-36,50,number,32,color,True);text(x+18,y+75,w-36,h-85,label,17)

new('End-to-End Performance\nModelling and Analysis','5G smart factory · AI-based quality inspection','Sun Jiangeng',25,
"Good morning. We are Sun Jiangeng, Qian Tu and Lu Zipeng. Our project investigates how images travel from industrial cameras to an edge server for AI-based quality inspection. We combine network routing, wireless polling and queueing theory. Our central question is whether a fast processing server is enough to guarantee timely delivery of every image.",True)
text(44,176,820,70,'Communication Networks • Continuous Assessment 1\n2026–2027',20,WHITE)
text(44,282,840,108,'Sun Jiangeng  |  202612491511\nQian Tu  |  202612491508\nLu Zipeng  |  202612491522',19,WHITE)
text(44,440,820,30,'A reproducible model, with explicit assumptions and measured uncertainty.',17,'A7B8C9')

new('Three tasks, one image journey','Project scope','Sun Jiangeng',35,
"The assessment has three connected tasks. First, we model cameras, base stations and the edge server as a graph and select a route. Second, we use Shannon's formula and a clearly specified polling schedule to derive wireless delay. Third, we analyse an M/M/1 server using Little's law. We then compare theory with Python simulations and examine the complete chain. Our results concern communication and processing delays; the AI classifier itself is outside the model.")
for x,n,label in [(42,'01','Graph model\nLink attributes and route selection'),(340,'02','Wireless access\nShannon rate and polling delay'),(638,'03','Queueing model\nM/M/1 and the arrival-rate limit')]:card(x,167,278,220,n,label)
text(44,426,855,54,'The integrated simulation checks whether the assumptions remain valid when the stages are connected.',21)

new('An illustrative, fully declared baseline','Inputs and assumptions','Sun Jiangeng',40,
"The brief does not specify numerical inputs, so these are declared design assumptions. We use four cameras, one-megabit images, twenty megahertz of bandwidth and a ten-decibel signal-to-noise ratio. The edge server processes fifty images per second on average. We choose one hundred milliseconds as an illustrative mean-time target. Camera arrivals are independent Poisson streams. Baseline images have fixed size, while edge processing times are exponential. These are distinct assumptions about two different stages of the system.")
for x,y,n,label in [(42,158,'4 cameras','Independent Poisson image arrivals'),(342,158,'1 Mbit','Fixed image size in baseline'),(642,158,'20 MHz','Scheduled bandwidth; SNR = 10 dB'),(42,327,'50 images/s','MEC mean service rate'),(342,327,'100 ms','Chosen mean-delay target'),(642,327,'0.20 ms','Grant / guard overhead per visit')]:card(x,y,276,148,n,label)

new('A graph makes the routing decision explicit','Task 1 · graph theory','Sun Jiangeng',55,
"Each camera, base station and server is a graph vertex. Directed edges represent possible uplink and backhaul links. Camera nodes carry an arrival rate and image size. The edge server carries its processing rate and queue discipline. Link attributes include capacity and propagation delay. Base station A can reach the server directly, or cooperate with base station B. Our example has one active camera cell, so the faster backhaul links do not develop queues. The wireless capacity shown here is available only while a camera is scheduled. It is not simultaneously available to all four cameras.")
picture('01_topology.png',42,142,874,325)
text(44,477,860,20,'Link weight = image serialization time + propagation delay. Source: report Section 3.',12,GRAY)

new('The extra hop is faster in this graph','Task 1 · Dijkstra result','Sun Jiangeng',45,
"We assign each link a nonnegative weight equal to image size divided by link capacity, plus propagation delay. Dijkstra's algorithm selects the smallest sum. The direct wired backhaul takes eleven milliseconds per image. The two-hop path takes only two point seven milliseconds because its links have higher capacity. Including the common wireless transmission, the selected route takes seventeen point one five milliseconds before polling and processing are added. It saves eight point three milliseconds. This is the shortest unloaded transmission route for this graph, rather than a guarantee about every possible congestion condition.")
card(42,172,420,157,'11.00 ms','Direct wired backhaul: A → MEC',GRAY)
card(490,172,426,157,'2.70 ms','Selected wired backhaul: A → B → MEC')
text(45,375,860,70,'Selected path: C1 → A → B → MEC\nTotal route weight: 17.15 ms; saving: 8.30 ms',24,TEAL,True)

new('Shannon gives the scheduled radio rate','Task 2 · transmission time','Qian Tu',45,
"I will explain the wireless model. Shannon's capacity formula is bandwidth multiplied by the base-two logarithm of one plus the linear signal-to-noise ratio. Ten decibels corresponds to a linear value of ten. With twenty megahertz, the result is sixty-nine point one nine megabits per second. A one-megabit image therefore takes fourteen point four five milliseconds to transmit. This is an ideal capacity calculation. Actual throughput can be lower because of coding, interference and retransmissions. Our model grants all resource blocks to one camera at a time, which is a simple OFDMA scheduling case.")
text(45,166,855,67,'R = W log₂(1 + SNRlinear)',34,TEAL,True)
card(42,265,420,160,'69.19 Mbit/s','Ideal payload rate while scheduled')
card(490,265,426,160,'14.45 ms','Transmission time τ = S / R')
text(45,455,855,35,'OFDMA resources are assigned in time; bandwidth is never counted four times.',17)

new('A visit is not immediately available','Task 2 · polling timing','Qian Tu',55,
"The base station visits cameras one to four cyclically. Each visit includes a grant interval and transmission of at most one image. An unused reservation remains idle. One visit lasts fourteen point six five milliseconds, and a full cycle lasts fifty-eight point six one milliseconds. Consider an isolated tagged image arriving at a random phase, with no older image waiting. Its mean residual wait is half a cycle. Adding the grant and transmission gives forty-three point nine six milliseconds. This particular formula assumes random arrival phase. A simultaneous batch at the start of a cycle would have a different average waiting time.")
picture('02_polling.png',42,145,874,263)
text(45,429,860,58,'C = N(g + τ) = 58.61 ms\nTagged mean wireless time = C/2 + g + τ = 43.96 ms',22,TEAL,True)

new('Camera backlog adds another load effect','Task 2 · queued polling','Qian Tu',55,
"At higher traffic loads, there may already be older images at the same camera. A new image can then miss more than one visit. For our reserved one-image polling rule, the exact mean wait is the cycle length divided by twice one minus the camera's visit utilisation. The report derives this using the queue observed after each visit and Little's law. At twenty-five images per second, the mean polling wait is forty-six point two five milliseconds. At forty images per second it is seventy point eight one milliseconds. The simulation agrees with this formula to within about zero point one four percent across the tested rates.")
text(45,161,860,65,'Mean polling wait = C / [2(1 − r)]',31,TEAL,True)
text(45,230,860,58,'r = (λ / N)C = λ(g + τ)\nRadio stability: λ < 68.24 images/s',22)
card(42,332,420,142,'46.25 ms','Mean polling wait at λ = 25/s')
card(490,332,426,142,'70.81 ms','Mean polling wait at λ = 40/s')

new('Test each model, then connect the stages','Reproducible simulation','Qian Tu',45,
"We use three experiments: the isolated M/M/1 server, the exact polling system and the actual connected chain. Each tested arrival rate has thirty independent replications. Each replication retains one hundred thousand images after a twenty-thousand-image warm-up. Confidence intervals are calculated from replication means, because delays within a run are correlated. Ten deterministic tests check the scheduling, queue recursion, route selection and lecture example. We also check that end-to-end delay equals the sum of its measured components. Lu will now explain the server analysis and the final results.")
for x,n,label in [(42,'30','Independent replications per rate'),(340,'100,000','Measured images per replication'),(638,'20,000','Warm-up images discarded')]:card(x,163,278,185,n,label)
text(45,390,850,75,'11 arrival rates • Fixed published seed • 95% confidence intervals\n10 deterministic tests passed; raw replication results included.',21)

new('The required M/M/1 mean-delay bound','Task 3 · queueing theory','Lu Zipeng',50,
"The server state counts waiting images plus the image being processed. Arrivals increase the state at rate lambda; completions reduce it at rate mu when the server is occupied. Stability requires lambda smaller than mu. Using the geometric stationary probabilities and Little's law gives mean system time one divided by mu minus lambda. This includes both waiting and processing. Setting that mean to at most one hundred milliseconds, with a service rate of fifty images per second, gives a maximum arrival rate of forty images per second. This bound applies to the isolated Poisson-input server, not automatically to the complete image journey.")
picture('03_states.png',42,137,874,200)
text(45,355,850,53,'T = Ws = Wq + 1/μ = 1/(μ − λ)',29,TEAL,True)
text(45,420,850,54,'λmax = μ − 1/Tmax = 40 images/s\nFeasibility: Tmax > 1/μ; stability: λ < μ.',22)

new('Theory and simulation agree at the server','Task 3 · numerical validation','Lu Zipeng',40,
"The curve shows the rapid increase in queueing delay as the arrival rate approaches the processing rate. Simulated means closely follow the theoretical values, with a maximum relative difference of zero point six two percent. At forty images per second, theory gives one hundred milliseconds and simulation gives ninety-nine point three eight milliseconds. Error bars represent pointwise ninety-five-percent confidence intervals. Ten of eleven intervals cover the theoretical mean. We report that outcome explicitly rather than adjusting random seeds to force all points to match.")
picture('04_mm1.png',42,137,680,349)
text(748,184,170,60,'0.62%',33,TEAL,True)
text(748,244,170,110,'Maximum relative difference in the mean',20)
text(748,375,170,78,'10 of 11 pointwise intervals cover theory.',16,GRAY)

new('The complete chain has a lower latency capacity','Integrated-chain result','Lu Zipeng',45,
"Connecting the stages changes the answer. At twenty-five images per second, mean end-to-end delay is ninety-eight point five two milliseconds. At thirty images per second, it rises to one hundred twelve point four eight milliseconds. Therefore twenty-five is the highest tested rate meeting the mean target, not a proven exact threshold. Polling changes the server's arrival statistics, so simply adding an M/M/1 server time is only an approximation. The component plot shows both camera waiting and server processing. Twenty images per second provides more operating margin in the baseline.")
picture('05_integrated.png',42,145,874,285)
text(45,449,870,42,'25 images/s: 98.52 ms     |     30 images/s: 112.48 ms',23,TEAL,True)

new('Upgrade radio and processing together','Optimisation at λ = 40 images/s','Lu Zipeng',40,
"We also compare four designs at the same offered load. The baseline mean is about one hundred seventy-four milliseconds. A faster server alone gives one hundred ten milliseconds, and more bandwidth alone gives one hundred twenty-eight milliseconds. Combining both upgrades gives fifty-seven point three one milliseconds, a reduction of about sixty-seven percent. However, about nine point five percent of images still exceed one hundred milliseconds. The combined upgrade meets the chosen mean target, while a strict reliability requirement would need further design work.")
with (ROOT/'results/optimization_summary.csv').open() as f:opt=list(csv.DictReader(f))
for i,r in enumerate(opt):
 y=157+i*74;value=float(r['mean_s'])*1000
 text(43,y+6,215,35,r['design'],19)
 rect(274,y+3,value*2.7,34,TEAL if i==3 else NAVY)
 text(284+value*2.7,y+6,170,33,f'{value:.2f} ms',19,TEAL if i==3 else NAVY,True)
text(45,460,860,32,'Combined upgrade: 40 MHz + 75 images/s MEC; deadline misses remain 9.51%.',18)

new('Design for the whole journey','Conclusions and questions','Lu Zipeng',25,
"Our conclusions are threefold. Route capacity matters as well as hop count. Polling delay increases with camera backlog. And an isolated server delay bound is not an end-to-end guarantee. Our code, diagrams and data make these findings reproducible. The next engineering step would be to measure real traffic and processing times, then specify a numerical reliability target. Thank you. We welcome your questions.",True)
text(45,163,865,175,'01  Choose routes using capacity and delay.\n\n02  Include both polling backlog and MEC queueing.\n\n03  Check mean delay and deadline reliability separately.',23,WHITE)
text(45,390,865,48,'Questions',30,'75D1D4',True)
text(45,455,850,42,'Sources: assessment brief; course Chapter 2; Shannon (1948); Dijkstra (1959); Little (1961). Full references and derivations are in the report.',12,'A7B8C9')

prs.save(OUT/'Communication_Networks_Presentation.pptx');cv.save()
(ROOT/'validation/slide_layout_checks.json').write_text(json.dumps(layout_checks,indent=2))
(ROOT/'slides/slide_notes.json').write_text(json.dumps(notes,indent=2))
s=['# Ten-minute presentation script','', 'Timing target: 600 seconds. Slides 1–5: Sun Jiangeng; 6–9: Qian Tu; 10–14: Lu Zipeng. Each member has 200 seconds. Rehearse and adjust pace; timings are targets, not measured delivery times.','']
for n in notes:s += [f"## Slide {n['slide']}. {n['title'].replace(chr(10),' ')}",'',f"**Speaker:** {n['speaker']} — **target:** {n['seconds']} seconds",'',n['script'],'']
s += ['# Suggested answers for the question session','',
'**Why use M/M/1 if polling changes the arrival process?** The assignment explicitly requires an M/M/1 node model. We validate that model separately, then simulate the actual scheduler-generated traffic. We do not claim its MEC input remains Poisson.','',
'**What does T include?** In the required M/M/1 task, T is Ws: waiting plus processing at the selected node. Our end-to-end result additionally includes camera polling, grant, radio transmission and backhaul.','',
'**Why is lambda max 40/s in one place but 25/s elsewhere?** Forty is the exact isolated-MEC mean-delay bound for mu=50 and Tmax=0.1. Twenty-five is the highest tested end-to-end rate below the same mean target. Upstream delays consume budget.','',
'**How can two backhaul hops be faster than one?** Each selected link is 1 Gbit/s rather than 100 Mbit/s. For a 1 Mbit image, two serializations and their propagation sum to 2.7 ms, compared with 11 ms directly.','',
'**Is this still OFDMA?** The SBS allocates all RBs to one camera in each visit, then changes the recipient in time. It is a simple central scheduling case; simultaneous multi-camera RB allocation would require different bandwidth and delay calculations.','',
'**Why not use (N−1)τ/2 for polling wait?** That expression describes a particular simultaneous batch or discrete camera position. Our reference image arrives at a random continuous phase, giving a residual wait of C/2. Queued images add backlog, so the loaded mean is C/[2(1−r)].','',
'**What if image sizes are exponential?** At fixed rate R, X/R is exponential with rate R/E[X]. A continuously available transmission server with Poisson input then has an M/M/1 model. Fixed overhead and polling change that simple model.','',
'**Why is the baseline MEC exponential when image size is fixed?** Radio payload duration and AI processing duration are different random variables. The required queue model assumes variable exponential processing, independently of the baseline radio image size.','',
'**Does a 100 ms mean imply every image meets 100 ms?** No. At the isolated-MEC boundary, about 36.8% exceed it. In our upgraded integrated example the miss fraction is about 9.51%. A reliability requirement needs its own probability target.','',
'**Are the inputs measured from a real factory?** No. They are explicit illustrative assumptions because the brief supplies no numerical values. The results are conditional on those inputs.','',
'**What is the main limitation?** Constant SNR and fixed cyclic reservations simplify real scheduling. Actual traffic, processing variability, retransmissions, competing cells and finite buffers must be measured or modelled before deployment.','',
'**Why do not all 95% intervals contain theory?** Confidence intervals have a repeated-sampling interpretation and are pointwise. With eleven intervals, universal coverage is not guaranteed. We report all results and retain the original seeds.','']
(ROOT/'documents/Presentation_Script_and_QA.md').write_text('\n'.join(s))
print('Created 14-slide PPTX, PDF handout, notes and Q&A.')
print('Script words:',sum(len(re.findall(r"\b[\w’'-]+\b",n['script'])) for n in notes))
print('Total target seconds:',sum(n['seconds'] for n in notes))
