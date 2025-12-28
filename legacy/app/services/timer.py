# # app/services/timer.py

# from sqlalchemy.orm import Session # type: ignore
# from sqlalchemy import func # type: ignore
# from datetime import datetime, timedelta
# from typing import Optional, Union, List
# from fastapi import HTTPException # FastAPIのHTTP例外を使用 # type: ignore
# from ..models.project import DBProjectTask, DBTimerLog, DBProject # 必要なモデルをインポート

# # ----------------------------------------------------
# # 💡 補助関数群
# # ----------------------------------------------------

# def get_db_task_by_ids(db: Session, project_id: int, task_id: int) -> DBProjectTask:
#     """プロジェクトIDとタスクID(task_template_id)からDBProjectTaskを取得する。"""
#     # DBProjectTask の複合キーを使って取得
#     # 複合主キーが (project_id, task_template_id) の場合を想定
#     db_task: DBProjectTask = db.get(DBProjectTask, (project_id, task_id))
    
#     if not db_task:
#         # FastAPI の標準的な例外処理を使用
#         raise HTTPException(
#             status_code=404, 
#             detail="Project Task not found with the given project and task IDs."
#         )
#     return db_task


# def get_active_timer_log(db: Session, project_task_id: int) -> Optional[DBTimerLog]:
#     """
#     指定された project_task_id の、完了していない（end_timeがNoneの）最新のタイマーログを取得する。
#     """
#     return db.query(DBTimerLog).filter(
#         DBTimerLog.project_task_id == project_task_id,
#         DBTimerLog.end_time.is_(None)
#     ).order_by(
#         DBTimerLog.start_time.desc()
#     ).first()


# def calculate_current_duration_minutes(start_time: datetime, stop_time: datetime) -> float:
#     """
#     開始時間と停止時間から、経過時間を分単位 (float) で計算する。
#     """
#     if stop_time <= start_time:
#         return 0.0
#     duration: timedelta = stop_time - start_time
#     return duration.total_seconds() / 60.0 


# def calculate_total_actual_time(db: Session, project_task_id: int) -> float:
#     """
#     指定されたタスクのすべてのタイマーログを集計し、実績合計時間 (float) を計算する。
#     """
#     # func.sum の結果が Float になることを期待
#     total_minutes = db.query(
#         func.sum(DBTimerLog.duration_minutes)
#     ).filter(
#         DBTimerLog.project_task_id == project_task_id
#     ).scalar()
    
#     # None の場合は 0.0 を返す
#     return float(total_minutes) if total_minutes is not None else 0.0


# # ----------------------------------------------------
# # 💡 主要関数：タイマー開始/停止
# # ----------------------------------------------------

# def start_timer(db: Session, project_id: int, task_id: int) -> DBTimerLog:
#     """
#     指定されたタスクのタイマーを開始し、t_timer_logにレコードを作成する。
#     """
#     db_task = get_db_task_by_ids(db, project_id, task_id)

#     # 既存の未完了ログがないかチェック
#     if get_active_timer_log(db, db_task.project_task_id):
#         raise HTTPException(status_code=400, detail="Timer is already running for this task.")

#     # ログを作成
#     new_log = DBTimerLog(
#         project_task_id=db_task.project_task_id,
#         start_time=datetime.now()
#     )
#     db.add(new_log)
    
#     # タスクの状態を「進行中」に更新
#     if db_task.status == "unstarted":
#         db_task.status = "in_progress"
#         db.add(db_task)
    
#     db.commit()
#     db.refresh(new_log)
    
#     return new_log


# def stop_timer(db: Session, project_id: int, task_id: int) -> DBTimerLog:
#     """
#     実行中のタイマーを停止し、実績時間を計算してログに保存、タスクの実績時間を更新する。
#     """
#     db_task = get_db_task_by_ids(db, project_id, task_id)
    
#     # 実行中のタイマーログを取得
#     active_log = get_active_timer_log(db, db_task.project_task_id)

#     if not active_log:
#         raise HTTPException(status_code=400, detail="No active timer found for this task.")

#     # 1. タイマーを停止し、経過時間を計算
#     stop_time = datetime.now()
#     active_log.end_time = stop_time
    
#     # 経過時間を分単位 (float) で計算
#     duration_minutes_float = calculate_current_duration_minutes(active_log.start_time, stop_time)
    
#     # 2. ログの duration_minutes を更新
#     active_log.duration_minutes = duration_minutes_float
#     db.add(active_log) # ログの更新をセッションに追加
    
#     # 3. 実績合計時間を再計算し、タスクを更新
#     # ログの duration_minutes が更新された後、合計時間を再計算
#     total_actual_minutes = calculate_total_actual_time(db, db_task.project_task_id)
    
#     db_task.actual_time_minutes = total_actual_minutes 
#     db.add(db_task) # タスクの更新をセッションに追加
    
#     # 4. コミットとリフレッシュ
#     db.commit() 
#     db.refresh(active_log) # 返り値のためにログをリフレッシュ
    
#     return active_log

# app/services/timer.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException
from ..models.project import DBProjectTask, DBTimerLog

# ----------------------------------------------------
# 💡 補助関数
# ----------------------------------------------------

def get_db_task(db: Session, project_id: int, task_template_id: int) -> DBProjectTask:
    """プロジェクトIDとテンプレートIDからタスクを取得"""
    db_task = db.query(DBProjectTask).filter(
        DBProjectTask.project_id == project_id,
        DBProjectTask.task_template_id == task_template_id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="指定されたタスクが見つかりません。")
    return db_task

def get_active_log(db: Session, project_task_id: int) -> Optional[DBTimerLog]:
    """計測中（end_timeがNULL）のログを取得"""
    return db.query(DBTimerLog).filter(
        DBTimerLog.project_task_id == project_task_id,
        DBTimerLog.end_time.is_(None)
    ).first()

# ----------------------------------------------------
# 💡 タイマー操作
# ----------------------------------------------------

def start_timer(db: Session, project_id: int, task_id: int) -> DBTimerLog:
    """タイマーを開始する"""
    db_task = get_db_task(db, project_id, task_id)
    
    # 二重開始チェック
    if get_active_log(db, db_task.project_task_id):
        raise HTTPException(status_code=400, detail="タイマーは既に動作中です。")

    new_log = DBTimerLog(
        project_task_id=db_task.project_task_id,
        start_time=datetime.now()
    )
    
    # タスクステータスを更新（もし未着手なら進行中に）
    if db_task.status == "未着手":
        db_task.status = "進行中"

    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def stop_timer(db: Session, project_id: int, task_id: int) -> DBTimerLog:
    """タイマーを停止し、実績時間を更新する"""
    db_task = get_db_task(db, project_id, task_id)
    active_log = get_active_log(db, db_task.project_task_id)

    if not active_log:
        raise HTTPException(status_code=400, detail="動作中のタイマーがありません。")

    # 1. 停止時間を記録
    active_log.end_time = datetime.now()
    
    # 2. 今回の経過時間を計算 (Float: 分単位)
    duration = active_log.end_time - active_log.start_time
    duration_min = duration.total_seconds() / 60.0
    active_log.duration_min = duration_min
    
    db.add(active_log)
    db.flush() # 一旦DBに反映（まだコミットしない）

    # 3. タスクの実績合計時間を再集計して更新
    # 💡 ログテーブルの duration_minutes を合計する
    total_min = db.query(func.sum(DBTimerLog.duration_min)).filter(
        DBTimerLog.project_task_id == db_task.project_task_id
    ).scalar() or 0.0

    # モデル定義に合わせたカラム名 (actual_time_min)
    db_task.actual_time_min = float(total_min)
    
    db.commit()
    db.refresh(active_log)
    return active_log