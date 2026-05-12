"""Task logging and parameter recording for reproducibility."""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class TaskLogger:
    """Records analysis parameters and steps for reproducibility."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.data_dir / "analysis_log.json"
        self.log: Dict[str, Any] = {"sessions": []}
        self._load()

    def _load(self):
        if self.log_path.exists():
            try:
                self.log = json.loads(self.log_path.read_text(encoding='utf-8'))
            except Exception:
                pass

    def _save(self):
        self.log_path.write_text(json.dumps(self.log, indent=2, ensure_ascii=False), encoding='utf-8')

    def start_session(self, name: str = "") -> str:
        sid = datetime.now().strftime("%Y%m%d_%H%M%S")
        session = {
            "id": sid,
            "name": name,
            "started": datetime.now().isoformat(),
            "steps": [],
            "parameters": {},
        }
        self.log["sessions"].append(session)
        self._save()
        return sid

    def log_step(self, session_id: str, step_name: str, params: Dict = None, result: Dict = None):
        step = {
            "name": step_name,
            "timestamp": datetime.now().isoformat(),
            "parameters": params or {},
            "result_summary": result or {},
        }
        for s in self.log["sessions"]:
            if s["id"] == session_id:
                s["steps"].append(step)
                break
        self._save()

    def get_session(self, session_id: str) -> Dict:
        for s in self.log["sessions"]:
            if s["id"] == session_id:
                return s
        return {}

    def list_sessions(self) -> List[Dict]:
        return [{"id": s["id"], "name": s["name"], "started": s["started"], "steps": len(s["steps"])}
                for s in self.log["sessions"]]
