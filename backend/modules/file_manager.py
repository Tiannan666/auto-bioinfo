"""File utilities for the analysis platform."""

import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict


def ensure_dir(path: Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_files(directory: Path, pattern: str = "*") -> List[Path]:
    return sorted(Path(directory).glob(pattern))


def find_file(directory: Path, keywords: List[str], extensions: List[str] = None) -> Path:
    """Find a file containing any of the keywords."""
    for f in Path(directory).iterdir():
        if f.is_file():
            name_lower = f.name.lower()
            if any(kw.lower() in name_lower for kw in keywords):
                if extensions is None or f.suffix.lower() in extensions:
                    return f
    return None


def get_project_dir(data_dir: Path, project_id: str) -> Path:
    return ensure_dir(Path(data_dir) / "projects" / project_id)


def zip_directory(source: Path, output: Path):
    """Create a zip archive of a directory."""
    source = Path(source)
    output = Path(output)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in source.rglob('*'):
            if f.is_file():
                zf.write(f, f.relative_to(source))


def safe_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    return "".join(c for c in name if c.isalnum() or c in '._- ').strip().replace(' ', '_')[:100]
