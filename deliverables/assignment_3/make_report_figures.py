from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/assignment3-mpl')
import csv,json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent;out=root/'results';f=out/'figures'
rows=list(csv.DictReader((out/'curve_data.csv').open()))
plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False})
z=np.load(out/'fig2_grid.npz');fig,ax=plt.subplots(figsize=(3.4,2.6));im=ax.pcolormesh(z['x'],z['y'],z['snr_db'],shading='auto',cmap='viridis',vmin=-40,vmax=40)
ax.scatter([2,-2],[0,0],c=['white','red'],marker='x');ax.annotate('Bob',(2,0),color='white');ax.annotate('Eve',(-2,0),color='red');ax.set(xlabel='x (m)',ylabel='y (m)');fig.colorbar(im,ax=ax,label='SNR (dB)');fig.tight_layout();fig.savefig(f/'report_map.pdf');plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(7,5.3))
for name,ls in [('Perfect CSI','-'),('ZF','--'),('Robust bound',':'),('LoS / one tap','-.')]:
 a=[r for r in rows if r['figure']=='3' and r['p']=='inf' and r['scheme']==name];axs[0,0].plot([float(r['snr_db']) for r in a],[float(r['rate']) for r in a],ls,label=name)
axs[0,0].set(xlabel='Normalized SNR parameter (dB)',ylabel='Rate (bit/s/Hz)',title='(a) Paper Fig.3 analogue, p=infinity');axs[0,0].legend(fontsize=6.8)
for vary in ['Bob','Eve']:
 a=[r for r in rows if r['figure']=='4' and r['p']=='inf' and r['vary']==vary];axs[0,1].plot([float(r['users']) for r in a],[float(r['rate']) for r in a],'o-',ms=2,label=vary+' candidates')
axs[0,1].set(xlabel='Number of candidates',ylabel='Rate (bit/s/Hz)',title='(b) Paper Fig.4 analogue, p=infinity');axs[0,1].legend(fontsize=6.8)
for eb in [0,.2,.4]:
 a=[r for r in rows if r['figure']=='5' and r['scheme']=='Multipath' and float(r['eps_b'])==eb];axs[1,0].plot([float(r['eps_e']) for r in a],[float(r['rate']) for r in a],label=f'epsilon B={eb}')
axs[1,0].set(xlabel='Eve channel-error radius',ylabel='Worst-case rate (bit/s/Hz)',title='(c) Paper Fig.5 analogue');axs[1,0].legend(fontsize=6.8)
for name,color in [('Perfect','#1565c0'),('ZF','#d32f2f'),('Robust','#222222')]:
 for S,ls in [('50','-'),('1','--')]:
  a=[r for r in rows if r['figure']=='6' and r['scheme']==name and r['S']==S];axs[1,1].plot([float(r['order']) for r in a],[float(r['rate']) for r in a],ls,color=color,label=f'{name}, S={S}')
axs[1,1].set(xlabel='Maximum reflection order',ylabel='Rate (bit/s/Hz)',title='(d) Paper Fig.6 analogue');axs[1,1].legend(fontsize=6,ncol=2)
for ax in axs.flat:ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(f/'report_results.pdf');fig.savefig(f/'report_results.png',dpi=180);plt.close(fig)
points=list(csv.DictReader((root/'benchmark_points.csv').open()));(out/'source_digitized_points.json').write_text(json.dumps(points,indent=2))
