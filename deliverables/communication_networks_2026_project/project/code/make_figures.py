"""Build the report/presentation figures from saved simulation results."""
from pathlib import Path
import os,csv,json
os.environ.setdefault('MPLCONFIGDIR','/tmp/communication-networks-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
C=json.loads((ROOT/'results/configuration.json').read_text())
BLUE='#17324D';TEAL='#087F8C';GOLD='#D58A1F';GRAY='#65758B';RED='#BD4B46'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,
                     'axes.labelcolor':BLUE,'text.color':BLUE,'axes.titleweight':'bold','axes.titlesize':13,
                     'legend.frameon':False,'savefig.facecolor':'white'})


def rows(name):
    with (ROOT/'results'/name).open() as f: return list(csv.DictReader(f))


def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=200,bbox_inches='tight')
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight');plt.close(fig)


def box(ax,x,y,label,w=1.15,h=.6,color=BLUE):
    ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=.04',fc=color,ec='none'))
    ax.text(x,y,label,ha='center',va='center',color='white',fontsize=11,weight='bold')


fig,ax=plt.subplots(figsize=(10,4.8));ax.axis('off');ax.set(xlim=(-1,9),ylim=(-.9,3.9))
for i,y in enumerate([3,2,1,0],1):
    box(ax,0,y,f'C{i}')
    ax.add_patch(FancyArrowPatch((.62,y),(2.3,1.5),arrowstyle='-|>',mutation_scale=14,color=TEAL,lw=2))
box(ax,3,1.5,'SBS A',w=1.3);box(ax,5.6,3,'SBS B',w=1.3);box(ax,8,1.5,'MEC',w=1.3)
for a,b in [((3.62,1.75),(4.96,2.8)),((6.24,2.8),(7.38,1.75))]:
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=16,color=TEAL,lw=3))
ax.add_patch(FancyArrowPatch((3.7,1.3),(7.3,1.3),arrowstyle='-|>',mutation_scale=14,color=GRAY,lw=1.8,linestyle='--'))
ax.text(4.05,2.85,'1 Gb/s\n0.2 ms',ha='center',fontsize=10)
ax.text(7,3.05,'1 Gb/s\n0.5 ms',ha='center',fontsize=10)
ax.text(5.5,1.02,'100 Mb/s; 1.0 ms propagation',ha='center',fontsize=10,color=GRAY)
ax.text(1.6,3.45,'Wireless uplink\n69.19 Mb/s while scheduled',ha='center',fontsize=10,color=TEAL)
ax.text(8,.7,'FCFS queue\nμ = 50 images/s',ha='center',fontsize=10)
ax.text(0,-.6,'Independent Poisson\nimage sources',ha='center',fontsize=10)
ax.text(5.4,-.22,'Selected backhaul: A → B → MEC = 2.70 ms/image\nDirect backhaul: A → MEC = 11.00 ms/image',ha='center',fontsize=11)
ax.set_title('Figure 1. Directed topology and the selected store-and-forward route',loc='left')
save(fig,'01_topology')

fig,ax=plt.subplots(figsize=(10,3.5));slot=C['slot_s']*1000;cycle=C['cycle_s']*1000
colors=[TEAL,BLUE,GOLD,GRAY]
for i in range(8):
    x=i*slot;ax.add_patch(Rectangle((x,.75),slot,.45,facecolor=colors[i%4],edgecolor='white'))
    ax.text(x+slot/2,.975,f'C{i%4+1}',ha='center',va='center',color='white',weight='bold')
arrival=.30*cycle;next_slot=cycle
ax.annotate('Tagged C1 image arrives',xy=(arrival,.75),xytext=(arrival,.25),ha='center',arrowprops={'arrowstyle':'->','color':RED},color=RED)
ax.annotate('',xy=(next_slot,1.5),xytext=(arrival,1.5),arrowprops={'arrowstyle':'<->','color':RED})
ax.text((arrival+next_slot)/2,1.62,'Wait for next C1 visit',ha='center',color=RED)
ax.annotate('',xy=(cycle,.05),xytext=(0,.05),arrowprops={'arrowstyle':'<->','color':BLUE})
ax.text(cycle/2,-.15,f'One cycle C = {cycle:.2f} ms',ha='center')
ax.text(1.5*cycle,1.6,f'Each slot: g + τ = {slot:.2f} ms\ng = 0.20 ms; τ = {C["transmission_s"]*1000:.2f} ms',ha='center',fontsize=10)
ax.set(xlim=(0,2*cycle),ylim=(-.35,2),xlabel='Time (ms)',yticks=[])
ax.spines['left'].set_visible(False);ax.set_title('Figure 2. Reserved cyclic polling; one image per camera visit',loc='left')
save(fig,'02_polling')

fig,ax=plt.subplots(figsize=(9,2.4));ax.axis('off');ax.set(xlim=(-.7,6.7),ylim=(-1,1.1))
for i in range(5):
    x=i*1.3;ax.add_patch(plt.Circle((x,0),.28,color=BLUE));ax.text(x,0,str(i),ha='center',va='center',color='white',fontsize=16)
    if i<4:
        ax.add_patch(FancyArrowPatch((x+.23,.19),(x+1.07,.19),connectionstyle='arc3,rad=-.35',arrowstyle='-|>',mutation_scale=14,color=TEAL,lw=2))
        ax.add_patch(FancyArrowPatch((x+1.07,-.19),(x+.23,-.19),connectionstyle='arc3,rad=-.35',arrowstyle='-|>',mutation_scale=14,color=GOLD,lw=2))
        ax.text(x+.65,.53,'λ',ha='center',fontsize=15,color=TEAL)
        ax.text(x+.65,-.63,'μ',ha='center',fontsize=15,color=GOLD)
ax.text(6,0,'⋯',fontsize=22,ha='center');ax.text(2.6,-.95,'State k = images waiting + the image being processed',ha='center',fontsize=11)
ax.set_title('Figure 3. M/M/1 birth–death chain (no departure from state 0)',loc='left')
save(fig,'03_states')

m=rows('mm1_summary.csv');x=np.array([float(r['arrival_rate']) for r in m]);y=np.array([float(r['Ws']) for r in m])*1000
err=np.array([float(r['Ws_ci95_half']) for r in m])*1000
fig,ax=plt.subplots(figsize=(8.5,4.6));dense=np.linspace(0,46,300)
ax.plot(dense,1000/(50-dense),color=TEAL,lw=2.3,label='M/M/1 theory: 1/(μ − λ)')
ax.errorbar(x,y,yerr=err,fmt='o',color=BLUE,ms=4.5,capsize=3,label='Simulation: mean ± 95% CI')
ax.axhline(100,color=RED,ls='--',label='Mean-time limit: 100 ms');ax.axvline(40,color=GRAY,ls=':')
ax.annotate('λmax = 40 images/s',xy=(40,100),xytext=(8,150),arrowprops={'arrowstyle':'->','color':GRAY})
ax.set(xlabel='Aggregate image arrival rate λ (images/s)',ylabel='Mean MEC system time (ms)',ylim=(0,230),xlim=(0,46))
ax.grid(alpha=.15);ax.legend(loc='upper left',fontsize=10)
ax.set_title('Figure 4. Isolated Poisson-input MEC: theory versus simulation',loc='left');fig.tight_layout();save(fig,'04_mm1')

m=rows('integrated_summary.csv');z=lambda key:np.array([float(r[key]) for r in m])
fig,(ax,bx)=plt.subplots(1,2,figsize=(11,4.3))
ax.errorbar(x,z('end_to_end')*1000,yerr=z('end_to_end_ci95_half')*1000,color=TEAL,fmt='o-',capsize=3,label='Actual polled chain')
ax.plot(x,z('poisson_mec_additive_prediction')*1000,'--',color=GOLD,label='Additive M/M/1 MEC estimate')
ax.axhline(100,color=RED,ls=':',label='100 ms mean limit')
ax.set(xlabel='λ (images/s)',ylabel='Mean end-to-end time (ms)');ax.legend(fontsize=9);ax.grid(alpha=.15)
bx.plot(x,z('poll_wait')*1000,'o-',color=BLUE,label='Camera polling queue')
bx.plot(x,z('theory_poll_wait')*1000,'--',color=GOLD,label='Exact polling mean')
bx.plot(x,z('mec_time')*1000,'s-',color=TEAL,label='MEC wait + processing')
bx.axhline((C['slot_s']+C['backhaul_s'])*1000,color=GRAY,ls=':',label='Grant + radio + backhaul')
bx.set(xlabel='λ (images/s)',ylabel='Mean component time (ms)');bx.legend(fontsize=9);bx.grid(alpha=.15)
fig.suptitle('Figure 5. Actual cyclic polling changes MEC arrival statistics',x=.07,ha='left',weight='bold');fig.tight_layout();save(fig,'05_integrated')

m=rows('service_shape.csv');fig,ax=plt.subplots(figsize=(7.5,3.8))
xx=np.arange(len(m));vals=[float(r['simulation_s'])*1000 for r in m];ci=[float(r['ci95_half'])*1000 for r in m]
ax.bar(xx,vals,width=.55,color=[BLUE,TEAL],label='Simulation',yerr=ci,capsize=4)
for i,r in enumerate(m):
    t=float(r['theory_s'])*1000;ax.plot([i-.32,i+.32],[t,t],color=GOLD,lw=3,label='Theory' if i==0 else None)
    ax.text(i,vals[i]+3,f'{vals[i]:.2f} ms',ha='center')
ax.set(xticks=xx,xticklabels=['Exponential service\nM/M/1','Fixed service\nM/D/1'],ylabel='Mean system time (ms)',ylim=(0,90))
ax.legend();ax.set_title('Figure 6. Same mean service time, different delay: λ = 35/s',loc='left');fig.tight_layout();save(fig,'06_service_shape')

fig,ax=plt.subplots(figsize=(8.2,4.3))
for mu,color in [(50,BLUE),(60,TEAL),(75,GOLD)]:
    xx=np.linspace(0,min(mu-3,68),250);ax.plot(xx,1000/(mu-xx),color=color,label=f'μ = {mu} images/s')
ax.axhline(100,color=RED,ls='--',label='MEC mean-time limit');ax.axvline(C['radio_capacity_images_s'],color=GRAY,ls=':',label='Reserved radio ceiling')
ax.set(xlabel='λ (images/s)',ylabel='Isolated MEC mean time (ms)',ylim=(0,250),xlim=(0,72))
ax.legend(fontsize=9);ax.grid(alpha=.15);ax.set_title('Figure 7. Faster MEC shifts the bottleneck toward radio access',loc='left');fig.tight_layout();save(fig,'07_sensitivity')
print('Created 7 figures in PNG and vector PDF formats.')
