from http.client import HTTPException
from sqlalchemy.orm import Session # type: ignore
from sqlalchemy import func, select # type: ignore
from ..models.project import DBProject, DBProjectTask, DBTimerLog, DBTaskTemplate
from ..models.master import DBTransitionRule
from ..schemas.project import ProjectCreate, TimerStart, TimerStop, TaskTemplateCreate
from datetime import datetime
from typing import Any, Dict, List

# ワークフローに必要な初期マスタデータ (ここではハードコード)
INITIAL_STATUS_ID = 1 # 企画中
INITIAL_TASK_IDS = [2, 3, 4, 5] # 例: 骨子確定、フック入力、収録、カット編集

def create_initial_project(db: Session, project_in: ProjectCreate) -> DBProject:
    """新しいプロジェクトを作成し、初期サブタスクを紐づける"""
    
    # 1. トーク骨子の初期データを空のJSONとして作成
    initial_scaffold = {
        "title_options": [], 
        "script_intro": {"text": "", "core_emotion": ""},
        "discussion_flow": []
    }
    
    # 2. 親プロジェクトのDBオブジェクトを作成
    db_project = DBProject(
        type_id=1, # 仮にプロジェクトタイプID=1とする
        current_status_id=INITIAL_STATUS_ID,
        theme=project_in.theme,
        input_angle_id=project_in.input_angle_id,
        scaffold_data=initial_scaffold,
        created_at=datetime.now()
    )
    db.add(db_project)
    db.flush() # project_idを取得するために一度flushする
    
    project_id = db_project.project_id
    
    # 3. 初期サブタスクを生成し、DBに登録
    # ※ 本来はm_task_templateから情報を取得しますが、ここではタスクIDを仮定します
    #    また、est_time_minもm_task_templateから取得する必要がありますが、ここでは仮定値を使用します
    for task_id in INITIAL_TASK_IDS:
        db_task = DBProjectTask(
            project_id=project_id,
            task_template_id=task_id,
            status="未着手",
            est_time_min=30 # 仮の見積もり時間
        )
        db.add(db_task)
    
    db.commit()
    db.refresh(db_project)
    
    return db_project

def get_project_by_id(db: Session, project_id: int) -> DBProject:
    """プロジェクトIDからプロジェクトとそのサブタスクを取得する"""
    return db.query(DBProject).filter(DBProject.project_id == project_id).first()

def check_and_transition_status(db: Session, project_id: int):
    """
    プロジェクトの現在のステータスと完了タスクに基づき、
    次のステータスへ自動遷移するかどうかをチェックし、実行する。
    """
    project = get_project_by_id(db, project_id)
    if not project or project.current_status_id == 6: # 完了ステータスはスキップ
        return False

    current_status_id = project.current_status_id

    # 1. 現在のステータスからの遷移ルールを取得
    rules: List[DBTransitionRule] = db.query(DBTransitionRule).filter(
        DBTransitionRule.current_status_id == current_status_id,
        DBTransitionRule.is_active == True
    ).all()

    if not rules:
        return False # 遷移ルールなし

    # 2. 完了しているタスクIDのリストを取得
    completed_task_ids = db.query(DBProjectTask.task_template_id).filter(
        DBProjectTask.project_id == project_id,
        DBProjectTask.status == '完了'
    ).all()
    # 結果を単純なIDリストに変換
    completed_ids_set = {id[0] for id in completed_task_ids}

    # 3. 各ルールに対して遷移条件をチェック
    for rule in rules:
        required_ids_set = set(rule.required_task_ids)

        # 遷移条件: 必要なタスクIDが、完了済みタスクIDに全て含まれているか
        if required_ids_set.issubset(completed_ids_set):
            
            # 4. 遷移実行
            project.current_status_id = rule.next_status_id
            db.add(project)
            db.commit()
            return True  # 遷移が実行されました
            
    return False # 遷移なし

# ----------------------------------------------------
# 💡 プロジェクト進捗率更新処理
# ----------------------------------------------------

def update_project_progress(db: Session, project_id: int):
    """
    プロジェクト内の完了タスク数に基づいて進捗率を計算し、t_projectを更新する。
    """
    db_project: DBProject = db.get(DBProject, project_id)
    if not db_project:
        raise ValueError("Project not found.")

    # 1. すべてのタスク数を取得
    total_tasks = db.query(DBProjectTask).filter(
        DBProjectTask.project_id == project_id
    ).count()

    # 2. 完了したタスク数を取得
    completed_tasks = db.query(DBProjectTask).filter(
        DBProjectTask.project_id == project_id,
        DBProjectTask.status == "completed"
    ).count()

    if total_tasks == 0:
        progress_rate = 0
    else:
        # 進捗率を計算 (0から100の整数で計算)
        progress_rate = int((completed_tasks / total_tasks) * 100)

    # 3. DBProjectのprogress_rateを更新
    db_project.progress_rate = progress_rate
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

# 💡 補足: DBProject モデルに progress_rate カラムがあることを前提としています。
#    もし定義していなければ、Step 3で修正が必要です。

# --- 補助関数：AIサマリーの保存（ai_generator.py から呼び出されることを想定） ---

def update_summary_in_project(db: Session, project_id: int, summary_data: Dict[str, Any]):
    """生成されたサマリーをプロジェクトテーブルに保存する"""
    db_project: DBProject = db.get(DBProject, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found for update.")

    # 辞書をJSONBとしてそのまま保存
    db_project.summary_data = summary_data
    db.add(db_project)
    db.commit()
    db.refresh(db_project)