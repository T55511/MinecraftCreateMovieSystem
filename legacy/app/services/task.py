from http.client import HTTPException
from sqlalchemy.orm import Session # type: ignore
from sqlalchemy import func, select # type: ignore
from ..models.project import DBProject, DBProjectTask, DBTimerLog, DBTaskTemplate
from ..models.master import DBTransitionRule
from ..schemas.project import ProjectCreate, TimerStart, TimerStop, TaskTemplateCreate, ProjectTask
from datetime import datetime
from typing import Optional, List

# ----------------------------------------------------
# 💡 タスクテンプレート CRUD 関数
# ----------------------------------------------------

def create_task_template(db: Session, template: TaskTemplateCreate) -> DBTaskTemplate:
    """
    新しいタスクテンプレートを作成する。
    """
    db_template = DBTaskTemplate(
        task_name=template.task_name,
        est_time_min=template.est_time_min,
        task_category=template.task_category
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def get_all_task_templates(db: Session) -> List[DBTaskTemplate]:
    """
    すべてのタスクテンプレートを取得する。
    """
    return db.query(DBTaskTemplate).all()

def update_task_template(db: Session, template_id: int, template_data: TaskTemplateCreate) -> DBTaskTemplate:
    """
    既存のタスクテンプレートを更新する。
    """
    db_template = db.get(DBTaskTemplate, template_id)
    if not db_template:
        raise ValueError("Task template not found.")

    # データを更新
    db_template.task_name = template_data.task_name
    db_template.est_time_min = template_data.est_time_min
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def delete_task_template(db: Session, template_id: int):
    """
    タスクテンプレートを削除する。
    """
    db_template = db.get(DBTaskTemplate, template_id)
    if not db_template:
        raise ValueError("Task template not found.")
        
    # 💡 参照チェック: 既存のプロジェクトタスクが参照している場合は削除を拒否するなどのロジックも追加可能だが、
    #    ここではシンプルに削除する
    db.delete(db_template)
    db.commit()
    # 削除が成功したことを示すために True を返す
    return True

# ----------------------------------------------------
# 💡 タスク完了処理
# ----------------------------------------------------

def complete_task(db: Session, project_id: int, task_id: int) -> DBProjectTask:
    """
    指定されたプロジェクトタスクのステータスを 'completed' に更新する。
    """
    db_task: DBProjectTask = db.query(DBProjectTask).filter(
        DBProjectTask.project_id == project_id,
        DBProjectTask.task_template_id == task_id
    ).first()

    if not db_task:
        raise ValueError("Task not found in this project.")
    
    if db_task.status == "completed":
        # すでに完了している場合は更新しない
        return db_task 

    # 状態を完了に更新
    db_task.status = "completed"
    db_task.completed_at = datetime.now()
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 💡 循環参照回避: project_main から関数を遅延インポートまたは引数で渡す
    # 最も簡単な方法: 必要な関数をローカルインポートする（ファイルの冒頭ではなく関数内で）
    from .project_main import update_project_progress

    # 完了後、プロジェクト全体の進捗率を更新する
    update_project_progress(db, project_id)
    
    return db_task

def get_filtered_project_tasks(
    db: Session,
    project_id: int, 
    status: Optional[str] = None
) -> List[DBProjectTask]:
    """
    指定されたプロジェクトのタスクリストを取得する。
    タスクの状態 (status) でフィルタリング可能。
    """
    
    # 1. プロジェクトの存在確認
    if not db.get(DBProject, project_id):
        raise HTTPException(status_code=404, detail="Project not found.")

    # 2. ベースクエリの作成
    query = db.query(DBProjectTask).filter(
        DBProjectTask.project_id == project_id
    )
    
    # 3. フィルタリングロジックの適用
    if status:
        query = query.filter(DBProjectTask.status == status)
    
    # 4. 実行
    return query.all()