"""Backend server entry point for PyInstaller-packaged application.

This is a self-contained server launcher. When compiled with PyInstaller,
it produces a standalone backend.exe that includes all Python dependencies.
"""

import os
import sys
import argparse
from pathlib import Path


def get_app_dir():
    """Get the writable application data directory."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base = Path(os.environ.get('BIOINFO_DATA_DIR', os.path.expanduser('~/BioInfoData')))
    else:
        base = Path(__file__).parent
    return base


def main():
    parser = argparse.ArgumentParser(description='BioInfo Platform Backend')
    parser.add_argument('--port', type=int, default=8000, help='Server port')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Bind address')
    parser.add_argument('--data-dir', type=str, default=None, help='Data directory')
    args = parser.parse_args()

    # Set data directory
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = get_app_dir()

    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir = data_dir / 'output'
    output_dir.mkdir(exist_ok=True)

    os.environ['BIOINFO_DATA_DIR'] = str(data_dir)

    # Add bundle path for PyInstaller
    if getattr(sys, 'frozen', False):
        bundle_dir = Path(sys._MEIPASS)
        if str(bundle_dir) not in sys.path:
            sys.path.insert(0, str(bundle_dir))

    # Ensure backend is importable
    backend_dir = Path(__file__).parent / 'backend'
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir.parent))

    print(f'BioInfo Platform Backend v0.3.0')
    print(f'Data directory: {data_dir}')
    print(f'Starting server on {args.host}:{args.port}...')

    import uvicorn
    from backend.main import app

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level='info',
        access_log=True,
    )


if __name__ == '__main__':
    main()
