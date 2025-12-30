from sqlalchemy.orm import Session
from sqlalchemy import select

from models import MPhase, MTaskTemplate, MCheckItem, MTaskCheckMap

DEFAULT_PHASES = [
    (1, "planning", "企画中"),
    (2, "recording", "収録中"),
    (3, "editing", "編集中"),
    (4, "review", "最終確認"),
    (5, "publish", "公開待ち"),
    (6, "completed", "完了"),
]

DEFAULT_TASK_TEMPLATES = [
    # (sort_order, task_name, phase_key, est_time_min, is_timer_target)
    (1, "企画", "planning", 30, True),
    (2, "収録", "recording", 60, True),
    (3, "編集", "editing", 180, True),
]

DEFAULT_CHECK_ITEMS = [
    (1, "尺は想定内か"),
    (2, "言い淀みが多すぎないか"),
    (3, "音割れしていないか"),
]

# タスク名→チェック項目ラベルを紐づけ（例）
DEFAULT_TASK_CHECK_MAP = {
    "収録": ["尺は想定内か", "言い淀みが多すぎないか", "音割れしていないか"],
}

def seed_phases(db: Session) -> None:
    existing = db.execute(select(MPhase.phase_key)).all()
    existing_keys = {row[0] for row in existing}

    for sort_order, phase_key, display_name in DEFAULT_PHASES:
        if phase_key in existing_keys:
            continue
        db.add(MPhase(
            phase_key=phase_key,
            display_name=display_name,
            description=None,
            sort_order=sort_order,
            is_active=True,
        ))
    db.commit()


def seed_task_templates(db: Session) -> None:
    phases = db.execute(select(MPhase)).scalars().all()
    phase_by_key = {p.phase_key: p for p in phases}

    existing = db.execute(select(MTaskTemplate.task_name)).all()
    existing_names = {row[0] for row in existing}

    for sort_order, task_name, phase_key, est, is_timer in DEFAULT_TASK_TEMPLATES:
        if task_name in existing_names:
            continue
        phase = phase_by_key.get(phase_key)
        if not phase:
            continue

        db.add(MTaskTemplate(
            task_name=task_name,
            phase_id=phase.phase_id,
            est_time_min=est,
            is_timer_target=is_timer,
            sort_order=sort_order,
            is_active=True,
        ))
    db.commit()


def seed_all(db: Session) -> None:
    seed_phases(db)
    seed_task_templates(db)
