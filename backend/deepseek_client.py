"""DeepSeek API client wrapper (OpenAI-compatible)."""

import os
import json
from pathlib import Path
from typing import List, Dict
import openai

from .bio_prompt import SYSTEM_PROMPT

DATA_DIR = Path(os.environ.get("BIOINFO_DATA_DIR", str(Path(__file__).parent.parent)))
CONFIG_PATH = DATA_DIR / "config.json"


def load_config() -> Dict:
    """Load configuration from config.json."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config: Dict) -> None:
    """Save configuration to config.json."""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_client() -> bool:
    """Configure and return True if API key is set."""
    config = load_config()
    api_key = config.get("deepseek_api_key", "")
    if not api_key:
        return False
    openai.api_key = api_key
    openai.api_base = "https://api.deepseek.com"
    return True


def chat(messages: List[Dict]) -> Dict:
    """
    Send messages to DeepSeek and get response.
    Returns: {"content": str, "error": str | None}
    """
    if not get_client():
        return {"content": "", "error": "请先在设置中配置 DeepSeek API Key"}

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    try:
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=full_messages,
            temperature=0.3,
            max_tokens=4096,
        )
        content = response.choices[0].message.content
        return {"content": content, "error": None}
    except Exception as e:
        error_msg = str(e)
        if "Insufficient Balance" in error_msg or "余额" in error_msg:
            error_msg = "DeepSeek 账户余额不足，请充值后再试。"
        elif "Authentication" in error_msg or "auth" in error_msg.lower():
            error_msg = "API Key 无效，请检查设置中的 DeepSeek API Key。"
        elif "rate" in error_msg.lower():
            error_msg = "请求频率过高，请稍后重试。"
        return {"content": "", "error": error_msg}
