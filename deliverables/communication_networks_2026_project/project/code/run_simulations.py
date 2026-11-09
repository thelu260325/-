"""Reproduce all numerical results with independent seeded replications.

Run: python code/run_simulations.py
All results are generated; no reference curve is substituted for simulation.
"""
from pathlib import Path
import argparse,csv,json,platform,time
import numpy as np
import scipy
from scipy.stats import t as student_t
from model import rate,mm1,fcfs_departures,polling_starts,waiting_area,shortest_path

ROOT=Path(__file__).resolve().parents[1]


def ci(x):
    x=np.asarray(x,dtype=float)
    half=student_t.ppf(.975,len(x)-1)*x.std(ddof=1)/np.sqrt(len(x))
    return float(x.mean()),float(half)


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def run(reps=30, samples=100000, warmup=20000):
    out=ROOT/'results';out.mkdir(exist_ok=True)
    start=time.perf_counter()
    cfg=dict(seed=20261109,replications=reps,measured_images_per_replication=samples,
             warmup_images=warmup,cameras=4,mean_size_bits=1e6,bandwidth_hz=20e6,
             snr_db=10.,poll_overhead_s=.0002,mec_service_rate=50.,deadline_s=.1,
             rates=[5.,10.,15.,20.,25.,30.,35.,37.5,40.,42.5,45.])
    R=float(rate(cfg['bandwidth_hz'],cfg['snr_db']));tx=cfg['mean_size_bits']/R
    slot=tx+cfg['poll_overhead_s'];cycle=cfg['cameras']*slot
    edges=[(f'C{i}','A',R,0.) for i in range(1,5)]+[('A','M',100e6,.001),('A','B',1e9,.0002),('B','M',1e9,.0005)]
    route,route_cost=shortest_path(edges,'C1','M',cfg['mean_size_bits'])
    backhaul=route_cost-tx
    cfg.update(rate_bps=R,transmission_s=tx,slot_s=slot,cycle_s=cycle,
               radio_capacity_images_s=1/slot,backhaul_s=backhaul,
               selected_route=route,selected_route_weight_s=route_cost)
    (out/'configuration.json').write_text(json.dumps(cfg,indent=2))
    raw=[];summary=[];integrated=[];raw_int=[];shape=[]
    for k,lam in enumerate(cfg['rates']):
        theory=mm1(lam,cfg['mec_service_rate'])
        node=[];chain=[]
        for j in range(reps):
            rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],1,k,j]))
            a=np.cumsum(rng.exponential(1/lam,samples+warmup))
            service=rng.exponential(1/cfg['mec_service_rate'],len(a))
            d=fcfs_departures(a,service)
            sel=slice(warmup,None);ws=d[sel]-a[sel];wq=ws-service[sel]
            # Finite-window Little audit includes all jobs intersecting the window.
            t0=a[warmup];t1=a[-1]
            L=waiting_area(a,d,t0,t1)/(t1-t0)
            observed_rate=(samples-1)/(t1-t0)
            entry=dict(arrival_rate=lam,replication=j,Ws=float(ws.mean()),Wq=float(wq.mean()),
                       deadline_miss_fraction=float((ws>cfg['deadline_s']).mean()),
                       time_average_L=L,little_relative_gap=float((L-observed_rate*ws.mean())/(observed_rate*ws.mean())))
            node.append(entry);raw.append(entry)

            # Actual integrated chain: independent Poisson camera arrivals,
            # reserved cyclic one-image polling, fixed two-hop backhaul,
            # FCFS exponential MEC processing. This input to MEC is NOT Poisson.
            rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],2,k,j]))
            camera_count=int(np.ceil((samples+warmup)*1.1/cfg['cameras']))
            arrivals=[];arr_mec=[];admitted=[]
            for camera in range(cfg['cameras']):
                ai=np.cumsum(rng.exponential(cfg['cameras']/lam,camera_count))
                starts=polling_starts(ai,cycle,camera*slot)
                arrivals.append(ai);admitted.append(starts)
                arr_mec.append(starts+slot+backhaul)
            # Common input-time cutoff prevents end-of-run loss of competing cameras.
            cutoff=min(x[-1] for x in arrivals)
            original=np.concatenate(arrivals);mec=np.concatenate(arr_mec);st=np.concatenate(admitted)
            valid=original<cutoff
            original,mec,st=original[valid],mec[valid],st[valid]
            order=np.argsort(mec,kind='stable');original,mec,st=original[order],mec[order],st[order]
            t_measure=np.sort(original)[warmup]
            mask=(original>=t_measure)&(original<np.sort(original)[warmup+samples])
            assert mask.sum()==samples
            assert mec[mask].max()<cutoff, 'Extend simulation: boundary can affect measured images'
            service=rng.exponential(1/cfg['mec_service_rate'],len(mec))
            d=fcfs_departures(mec,service)
            ws_mec=d[mask]-mec[mask];total=d[mask]-original[mask]
            intervals=np.diff(mec[(original>=t_measure)&(original<cutoff)])
            entry=dict(arrival_rate=lam,replication=j,poll_wait=float((st[mask]-original[mask]).mean()),
                       mec_time=float(ws_mec.mean()),end_to_end=float(total.mean()),
                       deadline_miss_fraction=float((total>cfg['deadline_s']).mean()),
                       mec_interarrival_scv=float(intervals.var()/intervals.mean()**2))
            chain.append(entry);raw_int.append(entry)
        nrow=dict(arrival_rate=lam,theory_Ws=theory['Ws'],theory_Wq=theory['Wq'],theory_Ls=theory['Ls'])
        for field in ['Ws','Wq','deadline_miss_fraction']:
            nrow[field],nrow[field+'_ci95_half']=ci([r[field] for r in node])
        nrow['relative_error']=(nrow['Ws']-theory['Ws'])/theory['Ws']
        nrow['theory_miss_fraction']=float(np.exp(-(cfg['mec_service_rate']-lam)*cfg['deadline_s']))
        nrow['mean_abs_little_gap']=float(np.mean([abs(r['little_relative_gap']) for r in node]))
        summary.append(nrow)
        rho_camera=lam/cfg['radio_capacity_images_s']
        irow=dict(arrival_rate=lam,theory_poll_wait=cycle/(2*(1-rho_camera)),
                  poisson_mec_additive_prediction=cycle/(2*(1-rho_camera))+slot+backhaul+theory['Ws'])
        for field in ['poll_wait','mec_time','end_to_end','deadline_miss_fraction','mec_interarrival_scv']:
            irow[field],irow[field+'_ci95_half']=ci([r[field] for r in chain])
        integrated.append(irow)
        print(f'lambda={lam:4.1f}: isolated MEC {nrow["Ws"]*1000:7.3f} ms; actual chain {irow["end_to_end"]*1000:7.3f} ms',flush=True)

    # Tagged no-backlog polling: arrival phase uniform over a reserved cycle.
    tagged=[]
    for j in range(reps):
        rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],3,j]))
        phase=rng.uniform(0,cycle,samples)
        tagged.append(float((cycle-phase+slot).mean()))
    tagged_mean,tagged_ci=ci(tagged)
    # Same mean service, different shape: M/D/1 vs M/M/1 at lambda=35.
    for kind in ['exponential','constant']:
        means=[]
        for j in range(reps):
            rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],4,j]))
            a=np.cumsum(rng.exponential(1/35,samples+warmup))
            s=rng.exponential(.02,len(a)) if kind=='exponential' else np.full(len(a),.02)
            means.append(float((fcfs_departures(a,s)[warmup:]-a[warmup:]).mean()))
        mean,half=ci(means)
        predicted=1/(50-35) if kind=='exponential' else .02+35/(2*50*(50-35))
        shape.append(dict(service_distribution=kind,arrival_rate=35,mean_service_s=.02,theory_s=predicted,simulation_s=mean,ci95_half=half))
    write_csv(out/'mm1_replications.csv',raw);write_csv(out/'mm1_summary.csv',summary)
    write_csv(out/'integrated_replications.csv',raw_int);write_csv(out/'integrated_summary.csv',integrated)
    write_csv(out/'service_shape.csv',shape)
    numerical=dict(tagged_polling_theory_s=cycle/2+slot,tagged_polling_mean_s=tagged_mean,tagged_polling_ci95_half=tagged_ci,
                   mm1_max_relative_error=float(max(abs(r['relative_error']) for r in summary)),
                   mm1_mean_deadline_lambda_max=50-1/.1,
                   integrated_tested_rates_meeting_mean_deadline=[r['arrival_rate'] for r in integrated if r['end_to_end']+r['end_to_end_ci95_half']<=.1],
                   runtime_s=time.perf_counter()-start,
                   versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__))
    (out/'summary.json').write_text(json.dumps(numerical,indent=2))
    print(json.dumps(numerical,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--replications',type=int,default=30)
    p.add_argument('--samples',type=int,default=100000);p.add_argument('--warmup',type=int,default=20000)
    a=p.parse_args()
    if a.replications<2 or a.samples<1000 or a.warmup<0: p.error('Invalid sample sizes')
    run(a.replications,a.samples,a.warmup)
