"""Run transparent, assumption-conditioned reproductions of Wang et al. Figs2–6.

No curves are fitted to the publication. Missing optical/timing parameters are
explicit. The solver independently optimizes the published objective, rather
than silently repairing or claiming to implement Algorithm1 verbatim.
"""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/assignment3-mpl')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import argparse,csv,json,time,platform
from dataclasses import asdict,replace
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from channel import ChannelConfig,VLCChannel,self_check
from beamforming import solve_beamforming,solve_zf,evaluate_rate,evaluate_metrics
from multiuser import solve_multiuser

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results';FIG=OUT/'figures'
PVALUES=(1,2,np.inf)
COLORS={1:'#1565c0',2:'#ef6c00',np.inf:'#00897b'}
RECORDS=[]

def dump(path,data):
 path.write_text(json.dumps(data,indent=2,default=lambda x:x.tolist() if hasattr(x,'tolist') else str(x)))

def keep(fig,stem):
 fig.tight_layout();fig.savefig(FIG/(stem+'.pdf'),bbox_inches='tight');fig.savefig(FIG/(stem+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)

def run(hb,he,p,snr=20,eb=0,ee=0,zf=False,**tag):
 result=(solve_zf(hb,he,snr,p) if zf else solve_beamforming(hb,he,snr,p,eb,ee))
 rec={**tag,'p':str(p),'snr_db':snr,'eps_b':eb,'eps_e':ee,'rate':result['rate'],'status':result['status']}
 for k in ['constraint_residual','conic_constraint_residual','dinkelbach_residual','residual','iterations','converged']:
  if k in result:rec[k]=result[k]
 RECORDS.append(rec)
 if not zf and not result.get('converged',True):raise RuntimeError(rec)
 return result

def main(skip_multi=False):
 start=time.time();OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'figure.figsize':(7,4.3)})
 cfg=ChannelConfig(max_reflections=6);model=VLCChannel(cfg)
 bob=(2.,0.,0.);eve=(-2.,0.,0.)
 b0=model.matrix(bob,max_reflections=0);e0=model.matrix(eve,max_reflections=0)
 gain_ref=float(np.linalg.norm(b0[0]))
 hb=model.matrix(bob,max_reflections=4)/gain_ref;he=model.matrix(eve,max_reflections=4)/gain_ref
 blo=b0/gain_ref;elo=e0/gain_ref
 np.savez_compressed(OUT/'channel_data.npz',HB=hb,HE=he,HB_LOS=blo,HE_LOS=elo,gain_ref_A=gain_ref)
 metadata={**model.metadata(),'normalization_reference_A':gain_ref,'normalization_definition':'Euclidean norm of nominal Bob direct-path first tap; same scalar for all receivers, orders and trials',
 'noise_axis':'20log10(alpha*g_ref/sigma_physical); equals normalized alpha/sigma, not asserted to be calibrated to original figure',
 'seed':cfg.seed,'reflection_surfaces':'four vertical walls only; floor/ceiling reflections omitted explicitly',
 'not_paper_inputs':['fixture coordinates','LED pitch','half-power angle','FoV','index','responsivity','wall reflectivity','patch/time resolution','symbol duration','normalization','multiuser distribution','position uncertainty radius']}
 dump(OUT/'configuration.json',metadata)
 print('CHANNEL ready; reference gain A=',gain_ref,flush=True)
 # Fig2 analogue: beam pattern over complete receiving plane, fixed Bob/Eve design.
 best=run(hb,he,np.inf,figure='2',scheme='perfect')
 axis=np.linspace(-4.9,4.9,31);Z=np.empty((len(axis),len(axis)))
 for iy,y in enumerate(axis):
  for ix,x in enumerate(axis):
   h=model.matrix((float(x),float(y),0),max_reflections=4)/gain_ref
   power=100*np.sum(np.sum(h*best['W'].T,axis=1)**2)
   Z[iy,ix]=10*np.log10(max(power,1e-12))
 np.savez_compressed(OUT/'fig2_grid.npz',x=axis,y=axis,snr_db=Z,W=best['W'])
 fig,ax=plt.subplots();im=ax.pcolormesh(axis,axis,Z,shading='auto',vmin=-40,vmax=40,cmap='viridis')
 ax.scatter([2,-2],[0,0],c=['white','red'],marker='x',s=65);ax.annotate('Bob',(2,0),color='white');ax.annotate('Eve',(-2,0),color='red')
 ax.set(xlabel='x (m)',ylabel='y (m)',title='Fig.2 analogue: optimized received-SNR map (assumed channel)');fig.colorbar(im,ax=ax,label='SNR (dB)');keep(fig,'fig2_snr_map')
 print('FIG2 complete',flush=True)
 # Fig3: exact same objective, three norm budgets; robust means worst-case not MC mean.
 x=np.arange(0,21,2);fig,ax=plt.subplots()
 for p in PVALUES:
  for name,zf,eb,ee,hb1,he1,ls in [('Perfect CSI',False,0,0,hb,he,'-'),('ZF',True,0,0,hb,he,'--'),('Robust bound',False,0,.05,hb,he,':'),('LoS / one tap',False,0,0,blo[:1],elo[:1],'-.')]:
   rates=[]
   for v in x:rates.append(run(hb1,he1,p,float(v),eb,ee,zf,figure='3',scheme=name)['rate'])
   ax.plot(x,rates,ls,color=COLORS[p],label=f'{name}, p={p}')
 ax.set(xlabel='Normalized 20 log10(alpha/sigma) (dB)',ylabel='Secrecy rate (bit/s/Hz)',title='Fig.3 analogue: power, budget and channel effects');ax.grid(alpha=.2);ax.legend(fontsize=6,ncol=2);keep(fig,'fig3_rates')
 print('FIG3 complete',flush=True)
 # Fig4: literally published sum-of-per-tap-maxima expressions. Shared user sets.
 rng=np.random.default_rng(cfg.seed)
 userB=np.vstack(([2.,0.,0.],np.c_[rng.uniform(.3,4.5,9),rng.uniform(-4.5,4.5,9),np.zeros(9)]))
 userE=np.vstack(([-2.,0.,0.],np.c_[rng.uniform(-4.5,-.3,9),rng.uniform(-4.5,4.5,9),np.zeros(9)]))
 B=np.stack([model.matrix(pos,max_reflections=4)/gain_ref for pos in userB]);E=np.stack([model.matrix(pos,max_reflections=4)/gain_ref for pos in userE])
 np.savez_compressed(OUT/'multiuser_channels.npz',B=B,E=E,positionsB=userB,positionsE=userE)
 if not skip_multi:
  fig,axes=plt.subplots(1,2,figsize=(8.2,3.4))
  for p in PVALUES:
   for which,ax in enumerate(axes):
    vals=[]
    for k in range(1,11):
     rr=solve_multiuser(B[:k] if which==0 else B[:1],E[:1] if which==0 else E[:k],20,p)
     RECORDS.append({'figure':'4','scheme':'published sum-of-maxima','p':str(p),'vary':'Bob' if which==0 else 'Eve','users':k,'rate':rr['rate'],'status':rr['status'],'residual':rr['residual'],'norm_violation':rr['norm_violation']})
     vals.append(rr['rate'])
    ax.plot(range(1,11),vals,'o-',ms=3,color=COLORS[p],label=f'p={p}')
    print('FIG4',p,'Bob' if which==0 else 'Eve','complete',flush=True)
  for ax,title,label in zip(axes,['Published Eq.(15): per-tap Bob selection','Published Eq.(14): per-tap worst Eve'],['Number of Bob candidates','Number of Eve candidates']):
   ax.set(xlabel=label,ylabel='Secrecy rate (bit/s/Hz)',title=title);ax.grid(alpha=.2);ax.legend(fontsize=7)
  keep(fig,'fig4_multiuser')
 # Fig5 robust exact spheres, not positional-circle Monte Carlo.
 fig,ax=plt.subplots();eps=np.linspace(0,.5,11)
 for eb,color in zip([0,.2,.4],['#1565c0','#ef6c00','#00897b']):
  for name,hb1,he1,ls in [('Multipath',hb,he,'-'),('LoS',blo[:1],elo[:1],'--')]:
   vals=[run(hb1,he1,np.inf,20,eb,float(ee),figure='5',scheme=name)['rate'] for ee in eps]
   ax.plot(eps,vals,ls,color=color,label=f'{name}, epsilon_B={eb}')
 ax.axhline(best['rate'],color='black',lw=1,label='Perfect-CSI upper bound');ax.set(xlabel='Normalized Eve uncertainty radius',ylabel='Worst-case secrecy rate (bit/s/Hz)',title='Fig.5 analogue: independent Euclidean uncertainty balls');ax.grid(alpha=.2);ax.legend(fontsize=7,ncol=2);keep(fig,'fig5_uncertainty')
 print('FIG5 complete',flush=True)
 # Fig6: make S=1 truncation vs a truly ISI-free DC baseline explicit.
 fig,ax=plt.subplots();orders=range(1,7)
 for scheme,color,zf,ee in [('Perfect','#1565c0',False,0),('ZF','#d32f2f',True,0),('Robust','#222222',False,.05)]:
  for S,ls in [(50,'-'),(1,'--')]:
   vals=[]
   for order in orders:
    bb=model.matrix(bob,S=S,max_reflections=order)/gain_ref;ev=model.matrix(eve,S=S,max_reflections=order)/gain_ref
    vals.append(run(bb,ev,np.inf,20,0,ee,zf,figure='6',scheme=scheme,S=S,order=order)['rate'])
   ax.plot(list(orders),vals,ls,color=color,label=f'{scheme}, S={S}')
 dc=[]
 for order in orders:
  bb=model.dc_gain(bob,order)[None,:]/gain_ref;ev=model.dc_gain(eve,order)[None,:]/gain_ref
  dc.append(run(bb,ev,np.inf,20,figure='6',scheme='ISI-free DC, all energy',S='DC',order=order)['rate'])
 ax.plot(list(orders),dc,':',color='#7b1fa2',label='ISI-free DC, retains all path energy')
 ax.set(xlabel='Maximum wall-reflection order',ylabel='Secrecy rate (bit/s/Hz)',title='Fig.6 analogue: reflections, tap truncation and retained energy');ax.legend(fontsize=7,ncol=2);ax.grid(alpha=.2);keep(fig,'fig6_reflections')
 print('FIG6 complete',flush=True)
 # Reproduce a literal Algorithm1/Proposition1 failure, independently of optics.
 a=np.ones(4)/4;cb=np.vstack((3*a,a));ce=np.vstack((.1*a,.7*a))
 paperW=np.ones((4,2));alternative=paperW.copy();alternative[:,1]=0
 counter={'construction_rate':evaluate_rate(cb,ce,paperW,0),'feasible_improvement_rate':evaluate_rate(cb,ce,alternative,0),
          'global_rate':run(cb,ce,np.inf,0,figure='audit',scheme='counterexample')['rate']}
 assert abs(counter['construction_rate']-.7591582015)<1e-9
 assert abs(counter['global_rate']-.8155449307)<1e-8
 # User-selection max/sum distinction.
 powers=np.array([[4.,1.],[1.,4.]])
 counter['sum_of_per_tap_maxima']=float(powers.max(axis=0).sum());counter['max_of_receiver_sums']=float(powers.sum(axis=1).max())
 # 1000 actual random positions, with an explicitly chosen geometric radius.
 robust=run(hb,he,np.inf,20,0,.05,figure='stress',scheme='1000-position test')
 angle=rng.uniform(0,2*np.pi,1000);radius=.25*np.sqrt(rng.uniform(0,1,1000));positions=np.c_[-2+radius*np.cos(angle),radius*np.sin(angle),np.zeros(1000)]
 rates=[];deviations=[]
 for pos in positions:
  hp=model.matrix(pos,max_reflections=4)/gain_ref
  rates.append(evaluate_rate(hb,hp,robust['W'],20));deviations.append(float(np.max(np.linalg.norm(hp-he,axis=1))))
 stress={'sample_size':1000,'eve_circle_radius_m':.25,'bob_fixed':True,'mean_rate':float(np.mean(rates)),'min_rate':float(np.min(rates)),'max_rate':float(np.max(rates)),'standard_error':float(np.std(rates,ddof=1)/np.sqrt(1000)),'designed_bound':robust['rate'],'fraction_inside_epsilon_ball':float(np.mean(np.array(deviations)<=.05+1e-10))}
 np.savez_compressed(OUT/'position_stress.npz',positions=positions,rates=rates,max_tap_deviation=deviations)
 # A spatial discretization check, without claiming temporal/global convergence.
 coarse=VLCChannel(replace(cfg,wall_patch_size=2));fine=VLCChannel(replace(cfg,wall_patch_size=.5))
 nominaldc=model.dc_gain(bob,4);finedc=fine.dc_gain(bob,4)
 mesh={'coarse_2m':coarse.dc_gain(bob,4).tolist(),'main_1m':nominaldc.tolist(),'fine_0_5m':finedc.tolist(),'relative_1m_vs_0_5m':float(np.linalg.norm(nominaldc-finedc)/np.linalg.norm(finedc))}
 dump(OUT/'counterexample.json',counter);dump(OUT/'position_stress.json',stress);dump(OUT/'mesh_check.json',mesh)
 # Comparison is descriptive: digitized source values are not fitted or raw data.
 benchfile=ROOT/'benchmark_points.csv'
 comparisons=[]
 if benchfile.exists():
  comparisons=list(csv.DictReader(benchfile.open()))
  dump(OUT/'source_digitized_points.json',comparisons)
 keys=sorted(set().union(*(d.keys() for d in RECORDS)))
 with (OUT/'curve_data.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,keys);w.writeheader();w.writerows(RECORDS)
 summary={'runtime_seconds':time.time()-start,'solver_records':len(RECORDS),'counterexample':counter,'position_stress':stress,'mesh':mesh,
 'main_perfect_rate_20dB_pinf':best['rate'],'main_robust_rate_20dB_pinf':robust['rate'],
 'python':platform.python_version(),'numpy':np.__version__,'scipy':__import__('scipy').__version__,'cvxpy':__import__('cvxpy').__version__,
 'scope':'Conditional independent reproduction of equation-level mechanisms and all five plot families; not exact data replay or original Algorithm1 implementation; unspecified parameters, normalized noise and different robust evaluation prevent claims of identical published curves.'}
 dump(OUT/'summary.json',summary)
 print('COMPLETE',json.dumps(summary,default=str),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--skip-multiuser',action='store_true');args=parser.parse_args();main(args.skip_multiuser)
