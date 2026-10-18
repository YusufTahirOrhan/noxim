"""Resumable parallel Noxim job runner for the DEFT_LB experiments.

A job is (name, args); the JSON statistics go to OUT/<name>.json. Existing
outputs are skipped. Returns the parsed JSON (or None on failure).
"""
import json
import os
import subprocess
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.abspath(os.path.join(HERE, '..', '..', 'bin'))
ENV = dict(os.environ, LD_LIBRARY_PATH=os.path.join(BIN, 'libs', 'systemc-2.3.1', 'lib-linux64'))
BASE_CONFIG = os.path.join(BIN, '..', 'config_examples', 'deft_2_5d_traffic_uniform.yaml')
LUT = os.path.join(HERE, 'luts', 'lut_rho001.yaml')


def mask_to_vls(mask):
    m = int(mask, 16)
    return ','.join(str(v) for v in range(64) if m >> v & 1)


def common_args(seed, mask, traffic=None, hardcoded=None, lut=None):
    a = ['-config', BASE_CONFIG, '-seed', str(seed), '-deft_vl_lut', lut or LUT,
         '-stats_format', 'json']
    vls = mask_to_vls(mask)
    if vls:
        a += ['-deft_faulty_vls', vls]
    if traffic:
        a += ['-traffic', 'table', traffic]
    if hardcoded:
        a += ['-traffic', 'hardcoded', hardcoded]
    return a


def _run(job):
    name, args, out_dir, timeout = job
    out = os.path.join(out_dir, name + '.json')
    if not os.path.exists(out):
        log = os.path.join(out_dir, name + '.log')
        try:
            with open(log, 'w') as lf:
                subprocess.run(['./noxim'] + args + ['-stats_file', out], cwd=BIN, env=ENV,
                               stdout=lf, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired:
            return name, None
        if os.path.exists(out):
            os.remove(log)
    try:
        return name, json.load(open(out))
    except Exception:
        return name, None


def run_jobs(jobs, out_dir, nproc=2, timeout=3600):
    os.makedirs(out_dir, exist_ok=True)
    with Pool(nproc) as pool:
        return dict(pool.imap_unordered(_run, [(n, a, out_dir, timeout) for n, a in jobs], chunksize=1))
