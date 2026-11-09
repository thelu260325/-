"""Audit completed outputs against analytical identities and numerical tolerances."""
from pathlib import Path
import csv,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def read(n):
    with (ROOT/'results'/n).open() as f:return list(csv.DictReader(f))
rows=read('mm1_summary.csv');integrated=read('integrated_summary.csv')
assert len(rows)==len(integrated)==11
assert max(abs(float(r['relative_error'])) for r in rows)<.02
assert max(float(r['mean_abs_little_gap']) for r in rows)<.001
assert all(float(r['Ws_ci95_half'])>0 for r in rows)
covered=sum(abs(float(r['Ws'])-float(r['theory_Ws']))<=float(r['Ws_ci95_half']) for r in rows)
poll_err=max(abs(float(r['poll_wait'])/float(r['theory_poll_wait'])-1) for r in integrated)
assert poll_err<.005
cfg=json.loads((ROOT/'results/configuration.json').read_text())
for r in integrated:
    assert abs(float(r['end_to_end'])-(float(r['poll_wait'])+cfg['slot_s']+cfg['backhaul_s']+float(r['mec_time'])))<1e-8
    assert float(r['end_to_end'])>float(r['mec_time'])
assert all(float(r['simulation_s'])>0 for r in read('service_shape.csv'))
result=dict(status='passed',mm1_points=len(rows),pointwise_CI_covering_theory=covered,
            maximum_poll_wait_relative_error=poll_err,
            note='Pointwise 95% intervals need not all cover the theoretical mean; no seeds were changed to force coverage.')
(ROOT/'validation/numerical_audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
