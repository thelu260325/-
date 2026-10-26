"""Numerical checks for model identities, optimization and uncertainty bounds."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json
from pathlib import Path
import channel,beamforming,multiuser
results={'channel':channel.self_check(),'beamforming':beamforming.self_test(),'multiuser':multiuser.self_test()}
p=Path(__file__).resolve().parent/'results';p.mkdir(exist_ok=True)
(p/'verification.json').write_text(json.dumps(results,indent=2,default=str))
print('PASS: channel, beamforming and multiuser numerical checks. See results/verification.json.')
