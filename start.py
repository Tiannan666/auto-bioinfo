"""Start script for the bioinformatics analysis tool."""

import os
import sys
import json
import webbrowser
import subprocess
from pathlib import Path

# Fix encoding on Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT = Path(__file__).parent

# Use writable data directory if provided (packaged app)
DATA_DIR = Path(os.environ.get("BIOINFO_DATA_DIR", str(ROOT)))
CONFIG_PATH = DATA_DIR / "config.json"
OUTPUT_DIR = DATA_DIR / "output"


def main():
    os.chdir(str(ROOT))

    # Parse arguments
    headless = "--headless" in sys.argv or "-H" in sys.argv

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("=" * 50)
    print("  生信分析助手 - 启动中...")
    if headless:
        print("  [headless 模式]")
    print("=" * 50)

    # Check dependencies
    try:
        import fastapi
        import uvicorn
        import openai
    except ImportError as e:
        print(f"\n缺少依赖: {e}")
        print("正在安装依赖...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"],
            check=True,
        )
        print("依赖安装完成，重新启动...\n")

    # Check config
    config_warning = False
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if not config.get("deepseek_api_key"):
            config_warning = True
    else:
        config_warning = True

    if config_warning:
        print("\n⚠ 未检测到 DeepSeek API Key!")
        print("  启动后请在设置页面填入 API Key")
        print("  获取地址: https://platform.deepseek.com/api_keys\n")

    url = "http://localhost:8000"
    print(f"启动服务: {url}")

    if not headless:
        webbrowser.open(url)

    # Start server
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
