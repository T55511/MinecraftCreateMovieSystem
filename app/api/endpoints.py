# app/api/endpoints.py

from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query # type: ignore
from sqlalchemy.orm import Session # type: ignore
from ..database import get_db
from ..schemas.project import Project, ProjectCreate, TimerStart, TimerStop, ProjectTask, TaskTemplate, TaskTemplateCreate
from ..schemas.ai import TalkScaffold, ProjectSummary
# from ..services.project import create_initial_project, get_project_by_id, check_and_transition_status, start_timer, stop_timer, complete_task, create_task_template, get_all_task_templates, update_task_template, delete_task_template
from ..services.project_main import (
    create_initial_project, 
    get_project_by_id, 
    check_and_transition_status
)
from ..services.task import (
    get_filtered_project_tasks, 
    complete_task, 
    create_task_template, 
    get_all_task_templates, 
    update_task_template, 
    delete_task_template
)
from ..services.timer import start_timer, stop_timer
from ..services.ai_generator import generate_talk_scaffold, update_scaffold_in_project, generate_thumbnail_concept, update_thumbnail_in_project, generate_project_summary, update_summary_in_project
from ..models.project import DBProject, DBProjectTask
from ..models.master import DBTaskTemplate # task_id の検証のため
from datetime import datetime

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

# --- プロジェクト作成エンドポイント ---
@router.post("/", response_model=Project)
def create_project(
    project: ProjectCreate, 
    db: Session = Depends(get_db)
):
    """新しいプロジェクトを作成し、初期サブタスクを生成する"""
    # 実際はここで入力angle_idのバリデーションが必要です
    
    db_project = create_initial_project(db, project)
    return db_project

# --- プロジェクト詳細取得エンドポイント (動作確認用) ---
@router.get("/{project_id}", response_model=Project)
def read_project(
    project_id: int, 
    db: Session = Depends(get_db)
):
    """プロジェクトIDでプロジェクト詳細を取得する"""
    project = get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# --- サブタスク完了エンドポイント ---
@router.put("/{project_id}/tasks/{task_id}/complete", response_model=Project)
def complete_project_task(
    project_id: int, 
    task_id: int, 
    db: Session = Depends(get_db)
):
    """
    サブタスクを「完了」に設定し、プロジェクトのステータス自動遷移をチェックする
    """
    
    # 1. 対象のサブタスクを取得
    db_task = db.query(DBProjectTask).filter(
        DBProjectTask.project_id == project_id,
        DBProjectTask.task_template_id == task_id
    ).first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found in this project.")

    # 2. ステータスを更新
    if db_task.status != '完了':
        db_task.status = '完了'
        db_task.completed_at = datetime.now()
        db.add(db_task)
        db.commit()

    # 3. ステータス自動遷移ロジックを実行
    transition_occurred = check_and_transition_status(db, project_id)
    
    # 4. 更新後のプロジェクト情報を返却
    updated_project = get_project_by_id(db, project_id)
    
    if transition_occurred:
        # 遷移が起きたことを示すメッセージなどをレスポンスに含めることも可能ですが、
        # ここでは更新されたプロジェクト情報を返します。
        print(f"Project {project_id} transitioned to status: {updated_project.current_status_id}")

    return updated_project

# --- トーク骨子生成エンドポイント ---
# 💡 修正: response_model=TalkScaffold を完全に削除し、戻り値の型ヒントも削除します。
@router.post("/{project_id}/scaffold", status_code=status.HTTP_200_OK)
def generate_and_save_scaffold( # 💡 戻り値の型ヒントを削除
    project_id: int, 
    db: Session = Depends(get_db)
):
    """
    指定プロジェクトのテーマとアングルに基づき、AIにトーク骨子を生成させ、保存する。
    """
    
    # 1. 骨子をAIに生成させる
    try:
        scaffold_data_dict = generate_talk_scaffold(db, project_id) 
    except ValueError as e:
        # APIキーが空の場合、この ValueError になる可能性が高い
        raise HTTPException(status_code=400, detail=str(e)) 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成中に予期せぬエラーが発生しました: {e}")

    # 2. 生成されたデータをDBに保存
    update_scaffold_in_project(db, project_id, scaffold_data_dict)
    
    # 3. 成功メッセージと、AIが生成したデータ（dict）をそのまま返す
    return {
        "message": "Talk scaffold successfully generated and saved.", 
        "data": scaffold_data_dict
    }

# --- サムネイルコンセプト生成エンドポイント ---
@router.post("/{project_id}/thumbnail", status_code=status.HTTP_200_OK)
def generate_and_save_thumbnail_concept(
    project_id: int, 
    db: Session = Depends(get_db)
):
    """
    指定プロジェクトのトーク骨子に基づき、AIにサムネイルコンセプトを生成させ、保存する。
    """
    
    # 1. コンセプトをAIに生成させる
    try:
        thumbnail_concept_dict = generate_thumbnail_concept(db, project_id) 
    except ValueError as e:
        # トーク骨子がない場合やAIパースエラーの場合
        raise HTTPException(status_code=400, detail=str(e)) 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成中に予期せぬエラーが発生しました: {e}")

    # 2. 生成されたデータをDBに保存
    update_thumbnail_in_project(db, project_id, thumbnail_concept_dict)
    
    # 3. 成功メッセージと、AIが生成したデータ（dict）をそのまま返す
    return {
        "message": "Thumbnail concept successfully generated and saved.", 
        "data": thumbnail_concept_dict
    }

# --- タイマー開始エンドポイント ---
@router.post("/{project_id}/tasks/{task_id}/start_timer", response_model=TimerStart)
def task_start_timer(
    project_id: int, 
    task_id: int, 
    db: Session = Depends(get_db)
):
    """タスクのタイマーを開始する"""
    try:
        db_log = start_timer(db, project_id, task_id)
        return TimerStart(project_task_id=db_log.project_task_id, start_time=db_log.start_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- タイマー停止エンドポイント ---
@router.post("/{project_id}/tasks/{task_id}/stop_timer", response_model=TimerStop)
def task_stop_timer(
    project_id: int, 
    task_id: int, 
    db: Session = Depends(get_db)
):
    """タスクのタイマーを停止し、実績時間を記録・集計する"""
    try:
        db_log = stop_timer(db, project_id, task_id)
        
        if db_log.end_time is None or db_log.duration_min is None:
            raise HTTPException(status_code=500, detail="Failed to calculate duration.")
        
        return TimerStop(
            project_task_id=db_log.project_task_id, 
            start_time=db_log.start_time,
            end_time=db_log.end_time,
            duration_min=db_log.duration_min
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- タスク完了エンドポイント ---
@router.post("/{project_id}/tasks/{task_id}/complete", response_model=ProjectTask)
def complete_task_endpoint(
    project_id: int, 
    task_id: int, 
    db: Session = Depends(get_db)
):
    """
    指定したプロジェクトタスクを完了状態に更新し、プロジェクトの進捗率を再計算する。
    """
    try:
        db_task = complete_task(db, project_id, task_id)
        
        # 完了後のタスク情報を返す
        return db_task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タスク完了処理中に予期せぬエラーが発生しました: {e}")

# --- 新規追加: タスクリスト取得（フィルタリング対応）エンドポイント ---
@router.get("/{project_id}/tasks/list", response_model=list[ProjectTask])
def get_project_tasks(
    project_id: int, 
    status: Optional[str] = Query(None, description="タスクのステータスでフィルタリング ('未着手', '進行中', 'completed' など)"),
    db: Session = Depends(get_db)
):
    """
    指定されたプロジェクトのタスクリストを取得する。
    タスクの状態 (status) でフィルタリング可能。
    """
    # 💡 修正: ロジックをサービス関数に委譲
    try:
        return get_filtered_project_tasks(db, project_id, status)
    except HTTPException as e:
        raise e

# --- サマリー生成エンドポイント ---
@router.post("/{project_id}/summary", status_code=status.HTTP_200_OK)
def generate_and_save_summary(
    project_id: int, 
    db: Session = Depends(get_db)
):
    """
    プロジェクトの終了データに基づき、AIにサマリーと反省点を生成させ、保存する。
    """
    
    # 1. サマリーをAIに生成させる
    try:
        summary_dict = generate_project_summary(db, project_id) 
    except ValueError as e:
        # データ不足やAIパースエラーの場合
        raise HTTPException(status_code=400, detail=str(e)) 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成中に予期せぬエラーが発生しました: {e}")

    # 2. 生成されたデータをDBに保存
    update_summary_in_project(db, project_id, summary_dict)
    
    # 3. 成功メッセージと、AIが生成したデータ（dict）をそのまま返す
    return {
        "message": "Project summary successfully generated and saved.", 
        "data": summary_dict
    }

# --- タスクテンプレート管理エンドポイント ---

@router.post("/templates", response_model=TaskTemplate, status_code=status.HTTP_201_CREATED)
def create_template_endpoint(
    template: TaskTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    新しいタスクテンプレートを作成する。
    """
    try:
        return create_task_template(db, template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"テンプレート作成中にエラーが発生しました: {e}")

@router.get("/templates", response_model=List[TaskTemplate])
def get_all_templates_endpoint(
    db: Session = Depends(get_db)
):
    """
    すべてのタスクテンプレートリストを取得する。
    """
    return get_all_task_templates(db)

@router.put("/templates/{template_id}", response_model=TaskTemplate)
def update_template_endpoint(
    template_id: int,
    template: TaskTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    指定されたIDのタスクテンプレートを更新する。
    """
    try:
        return update_task_template(db, template_id, template)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"テンプレート更新中にエラーが発生しました: {e}")

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template_endpoint(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    指定されたIDのタスクテンプレートを削除する。
    """
    try:
        delete_task_template(db, template_id)
        # 204 No Content はレスポンスボディを返さない
        return
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"テンプレート削除中にエラーが発生しました: {e}")