"""Safe Python code execution sandbox for bioinformatics analysis."""

import os
import re
import uuid
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass, field

from .bio_prompt import ALLOWED_IMPORTS, FORBIDDEN_PATTERNS

DATA_DIR = Path(os.environ.get("BIOINFO_DATA_DIR", str(Path(__file__).parent.parent)))
OUTPUT_DIR = DATA_DIR / "output"


@dataclass
class ExecutionResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    images: List[str] = field(default_factory=list)
    error: str = ""


def validate_code(code: str) -> Tuple[bool, str]:
    """Check code for forbidden patterns. Returns (is_safe, reason)."""
    lines = code.split('\n')

    for i, line in enumerate(lines, 1):
        # Check for forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in line:
                return False, f"Line {i}: forbidden pattern '{pattern}' detected"

    # Check imports against whitelist
    import_pattern = re.compile(
        r'^\s*(?:import\s+([\w.]+)|from\s+([\w.]+)\s+import)'
    )
    for i, line in enumerate(lines, 1):
        m = import_pattern.match(line)
        if m:
            module = m.group(1) or m.group(2)
            base_module = module.split('.')[0]
            # Check if base module or full module path is allowed
            allowed = False
            for allowed_mod in ALLOWED_IMPORTS:
                if module == allowed_mod or module.startswith(allowed_mod + '.') or allowed_mod.startswith(module + '.'):
                    allowed = True
                    break
            if not allowed:
                return False, f"Line {i}: import '{module}' is not in the allowed list"

    return True, "ok"


def extract_code_blocks(text: str) -> List[str]:
    """Extract Python code blocks from markdown text."""
    pattern = re.compile(r'```python\n(.*?)```', re.DOTALL)
    return pattern.findall(text)


def run_code(code: str, timeout: int = 120) -> ExecutionResult:
    """Execute Python code in a subprocess sandbox and capture results."""
    # Validate code safety
    is_safe, reason = validate_code(code)
    if not is_safe:
        return ExecutionResult(
            success=False,
            error=f"Code rejected by security check: {reason}"
        )

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Record existing files in output dir to detect new ones
    existing_files = set(OUTPUT_DIR.iterdir()) if OUTPUT_DIR.exists() else set()

    # Write code to temp file in output directory
    script_id = uuid.uuid4().hex[:8]
    script_path = OUTPUT_DIR / f"_script_{script_id}.py"

    # Wrap code to ensure output directory is correct
    wrapped_code = f"""
import os
os.chdir(r'{OUTPUT_DIR}')
os.makedirs('{OUTPUT_DIR}', exist_ok=True)

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

{code}
"""
    script_path.write_text(wrapped_code, encoding='utf-8')

    try:
        result = subprocess.run(
            ['python', str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(OUTPUT_DIR),
            env={**os.environ, 'MPLBACKEND': 'Agg'},
        )

        # Detect newly created image files
        current_files = set(OUTPUT_DIR.iterdir())
        new_files = current_files - existing_files - {script_path}
        images = sorted([
            f.name for f in new_files
            if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.svg', '.pdf', '.gif')
        ])

        return ExecutionResult(
            success=result.returncode == 0,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            images=[f"output/{img}" for img in images],
            error="" if result.returncode == 0 else result.stderr.strip(),
        )

    except subprocess.TimeoutExpired:
        return ExecutionResult(
            success=False,
            error=f"Code execution timed out after {timeout} seconds"
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            error=f"Execution error: {str(e)}"
        )
    finally:
        # Clean up temp script
        try:
            script_path.unlink(missing_ok=True)
        except Exception:
            pass
