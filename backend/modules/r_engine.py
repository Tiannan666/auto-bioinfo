"""
R engine bridge via subprocess (Rscript).
Auto-detects R installation. Falls back gracefully if R not available.
"""

import os, sys, tempfile, subprocess
from pathlib import Path


def _find_rscript() -> str:
    candidates = []
    if getattr(sys, 'frozen', False):
        # Packaged app: look in runtime/R, then userData/runtime/R
        candidates.append(str(Path(sys.executable).parent / 'runtime' / 'R' / 'bin' / 'Rscript.exe'))
        candidates.append(str(Path(os.environ.get('BIOINFO_DATA_DIR', '.')) / 'runtime' / 'R' / 'bin' / 'Rscript.exe'))
    candidates.extend([
        str(Path(__file__).parent.parent.parent / 'runtime' / 'R' / 'bin' / 'Rscript.exe'),
        'C:/Program Files/R/R-4.6.0/bin/Rscript.exe',
        'C:/Program Files/R/R-4.4.3/bin/Rscript.exe',
    ])
    for c in candidates:
        p = Path(c)
        if p.exists():
            return str(p)
    # Check system PATH
    for d in os.environ.get('PATH', '').split(os.pathsep):
        p = Path(d) / 'Rscript.exe'
        if p.exists():
            return str(p)
    return ''


_RSCRIPT = None
_AVAILABLE = None


def r_available() -> bool:
    global _AVAILABLE
    if _AVAILABLE is None:
        _AVAILABLE = bool(_find_rscript())
    return _AVAILABLE


def rscript_exe() -> str:
    global _RSCRIPT
    if _RSCRIPT is None:
        _RSCRIPT = _find_rscript()
    return _RSCRIPT


def run_r(code: str, timeout: int = 300) -> str:
    if not r_available():
        raise RuntimeError('R not available')
    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False, encoding='utf-8')
    tf.write(code); tf.close()
    try:
        r = subprocess.run([rscript_exe(), '--no-save', '--no-restore', tf.name],
                          capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            raise RuntimeError(r.stderr[:500] or 'Unknown R error')
        return r.stdout
    finally:
        try: os.unlink(tf.name)
        except: pass
