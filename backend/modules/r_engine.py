"""R engine via subprocess (Rscript). Lazy-init, no crash at import."""

import os, sys, tempfile, subprocess
from pathlib import Path

_rscript = None

def _find():
    r_home = os.environ.get('R_HOME', '')
    if r_home:
        direct = Path(r_home) / 'bin' / 'Rscript.exe'
        if direct.exists():
            return str(direct)
    bases = [r_home, 'C:/Program Files/R']
    for base in bases:
        if not base:
            continue
        p = Path(base)
        if not p.exists():
            continue
        for d in sorted(p.glob('R-*'), reverse=True):
            exe = d / 'bin' / 'Rscript.exe'
            if exe.exists():
                return str(exe)
    for d in os.environ.get('PATH', '').split(os.pathsep):
        exe = Path(d) / 'Rscript.exe'
        if exe.exists():
            return str(exe)
    return None

def r_available():
    global _rscript
    if _rscript is None:
        _rscript = _find()
    return _rscript is not None

def run_r(code, timeout=300):
    global _rscript
    if _rscript is None:
        _rscript = _find()
    if not _rscript:
        raise RuntimeError('R not found. Please install R first.')
    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False, encoding='utf-8')
    tf.write(code); tf.close()
    try:
        r = subprocess.run([_rscript, '--no-save', '--no-restore', tf.name],
                          capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            raise RuntimeError(r.stderr[:500] or 'R error')
        return r.stdout
    finally:
        try: os.unlink(tf.name)
        except: pass
