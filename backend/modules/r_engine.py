"""R engine via subprocess (Rscript). Assumes R + Bioconductor are installed."""

import os, sys, tempfile, subprocess
from pathlib import Path

def find_rscript():
    bases = [os.environ.get('R_HOME', ''), 'C:/Program Files/R']
    for base in bases:
        if not base: continue
        for d in sorted(Path(base).glob('R-*'), reverse=True):
            exe = d / 'bin' / 'Rscript.exe'
            if exe.exists(): return str(exe)
    # Check PATH
    for d in os.environ.get('PATH','').split(os.pathsep):
        exe = Path(d) / 'Rscript.exe'
        if exe.exists(): return str(exe)
    raise RuntimeError('R not found. Install R first.')

_rscript = None

def rscript():
    global _rscript
    if _rscript is None: _rscript = find_rscript()
    return _rscript

def run_r(code, timeout=300):
    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False, encoding='utf-8')
    tf.write(code); tf.close()
    try:
        r = subprocess.run([rscript(), '--no-save', '--no-restore', tf.name],
                          capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            raise RuntimeError(r.stderr[:500] or 'R error')
        return r.stdout
    finally:
        try: os.unlink(tf.name)
        except: pass

print(f'[R Engine] Rscript: {rscript()}')
