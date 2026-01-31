from sqlalchemy.orm import Session
from sqlalchemy import select

from models import TProject, TProjectTask


def recalc_project_progress(db: Session, project_id: int):
    tasks = db.execute(
        select(TProjectTask.status)
        .where(TProjectTask.project_id == project_id)
        .where(TProjectTask.is_active == True)
    ).all()

    if not tasks:
        rate = 0.0
    else:
        score = 0.0
        for (status,) in tasks:
            if status == "完了":
                score += 1.0
            elif status == "進行中":
                score += 0.5
        rate = (score / len(tasks)) * 100.0
        print(f"Project ID: {project_id}, score: {score}, total tasks: {len(tasks)}")

    project = db.execute(
        select(TProject).where(TProject.project_id == project_id)
    ).scalar_one()
    project.progress_rate = float(round(rate, 1))
