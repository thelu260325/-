"""Controlled integrated-chain sensitivity at lambda=40 images/s.

Uses the identical polling rule and independent exponential MEC service.
Common random numbers are used across designs, not across replications.
"""
from pathlib import Path
import csv,json
import numpy as np
from scipy.stats import t
from model import rate,polling_starts,fcfs_departures
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'results/configuration.json').read_text())
summary=[];raw=[]
for label,bw,mu in [('Baseline',20e6,50),('Faster MEC',20e6,75),('More bandwidth',40e6,50),('Both upgrades',40e6,75)]:
    sample=[];slot=1e6/rate(bw,10)+.0002;cycle=4*slot
    for j in range(30):
        rng=np.random.default_rng(np.random.SeedSequence([20261109,5,j]))
        arrivals=[];mecs=[]
        for i in range(4):
            a=np.cumsum(rng.exponential(.1,34000))
            arrivals.append(a);mecs.append(polling_starts(a,cycle,i*slot)+slot+.0027)
        cutoff=min(a[-1] for a in arrivals)
        a=np.concatenate(arrivals);m=np.concatenate(mecs);ok=a<cutoff;a,m=a[ok],m[ok]
        order=np.argsort(m);a,m=a[order],m[order];s=rng.exponential(1/mu,len(m));d=fcfs_departures(m,s)
        sorted_a=np.sort(a);mask=(a>=sorted_a[20000])&(a<sorted_a[120000])
        assert mask.sum()==100000 and m[mask].max()<cutoff
        total=d[mask]-a[mask]
        r=dict(design=label,replication=j,mean_s=float(total.mean()),miss_fraction=float((total>.1).mean()))
        raw.append(r);sample.append(r)
    row=dict(design=label,bandwidth_hz=bw,mec_rate=mu,arrival_rate=40)
    for key in ['mean_s','miss_fraction']:
        x=np.array([r[key] for r in sample]);row[key]=float(x.mean())
        row[key+'_ci95_half']=float(t.ppf(.975,29)*x.std(ddof=1)/np.sqrt(30))
    summary.append(row)
for name,data in [('optimization_summary.csv',summary),('optimization_replications.csv',raw)]:
    with (ROOT/'results'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
print(json.dumps(summary,indent=2))
