# v2/api/services/event_log_replay.py
import json
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from models import TEventLog

def replay_file_to_db(db: Session, file_path: str) -> int:
    p = Path(file_path)
    if not p.exists():
        return 0

    count = 0
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            e = json.loads(line)

            stmt = insert(TEventLog).values(
                event_id=e["event_id"],
                timestamp=e["timestamp"],  # ※DB側が timestamptz なら、fromisoformatにした方が確実
                level=e["level"],
                event_type=e.get("event_type", "audit"),
                request_id=e.get("request_id"),
                actor=e.get("actor", "local-user"),
                action=e["action"],
                target_type=e["target_type"],
                target_id=e.get("target_id"),
                summary=e["summary"],
                detail=e.get("detail"),
            ).on_conflict_do_nothing(index_elements=["event_id"])

            db.execute(stmt)
            count += 1

    db.commit()
    return count
