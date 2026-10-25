"""Resumable parallel Noxim job runner for the DEFT_LB experiments.

A job is (name, args); the JSON statistics go to OUT/<name>.json. Existing
outputs are skipped. Returns the parsed JSON (or None on failure).

Sharding (v10): `--shard i/n` anywhere on the command line of a script that uses
run_jobs (removed from sys.argv at import) runs only part i (0-based) of n of every
job list. The partition is deterministic: jobs are sorted by name and job k of the
sorted list belongs to shard k mod n. Each run is fully determined by its arguments
(seed included), so the results are the same on any machine with the same toolchain;
merge the per-shard CSVs with merge_csv.py.
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool


def _take_shard_arg():
    for k, a in enumerate(sys.argv):
        if a == '--shard' and k + 1 < len(sys.argv):
            i, n = (int(x) for x in sys.argv[k + 1].split('/'))
            del sys.argv[k:k + 2]
            assert 0 <= i < n
            return i, n
        if a.startswith('--shard='):
            i, n = (int(x) for x in a.split('=', 1)[1].split('/'))
            del sys.argv[k]
            assert 0 <= i < n
            return i, n
    return None


SHARD = _take_shard_arg()


def shard_jobs(jobs, shard=None):
    """The deterministic part of the job list for shard (i, n) (default: --shard of the command line)."""
    shard = shard or SHARD
    if not shard:
        return list(jobs)
    i, n = shard
    return [j for k, j in enumerate(sorted(jobs, key=lambda j: j[0])) if k % n == i]

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
    jobs = shard_jobs(jobs)
    with Pool(nproc) as pool:
        return dict(pool.imap_unordered(_run, [(n, a, out_dir, timeout) for n, a in jobs], chunksize=1))
