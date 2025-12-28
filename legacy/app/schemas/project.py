# app/schemas/project.py

from pydantic import BaseModel, Field, ConfigDict # type: ignore
from typing import Optional, Any
from datetime import datetime, timedelta

# --- 入力スキーマ (プロジェクト作成時) ---
class ProjectCreate(BaseModel):
    """プロジェクト作成に必要な入力データ"""
    theme: str = Field(..., description="トークテーマ")
    input_angle_id: int = Field(..., description="パーソナルアングルのID")
    # type_id は初期は固定（例: 1）とするか、別途マスタから選択する

# --- 出力スキーマ (サブタスク) ---
class ProjectTask(BaseModel):
    project_task_id: int
    task_template_id: int
    status: str
    est_time_min: int
    actual_time_min: Optional[float] = None
    completed_at: Optional[datetime] = None
    actual_time_min: float = Field(0.0, description="このタスクに費やした合計実績時間（分）")
    
    class Config:
        from_attributes = True

# --- 出力スキーマ (プロジェクト全体) ---
class Project(BaseModel):
    project_id: int
    current_status_id: int
    theme: str
    input_angle_id: int
    progress_rate: int = Field(0, description="プロジェクトの全体進捗率 (0-100)")
    scaffold_data: Any # JSONBフィールドはAnyで受け取る
    created_at: datetime
    tasks: list[ProjectTask] = [] # 紐づくサブタスクのリスト
    tasks: list[ProjectTask] = [] # 💡 ProjectTask スキーマを使用
    
    model_config = ConfigDict(from_attributes=True, extra='ignore') # 不要なフィールドを無視する設定

# --- タイマー操作用のスキーマ ---
class TimerStart(BaseModel):
    """タイマー開始時のレスポンス"""
    project_task_id: int
    start_time: datetime
    message: str = "Timer started successfully."

class TimerStop(BaseModel):
    """タイマー停止時のレスポンス"""
    project_task_id: int
    start_time: datetime
    end_time: datetime
    duration_min: float
    message: str = "Timer stopped and log saved."

# --- タスクテンプレートのマスタデータ用スキーマ ---
class TaskTemplateBase(BaseModel):
    task_name: str = Field(..., description="タスクテンプレート名 (例: 企画・構成案作成)")
    est_time_min: int = Field(..., description="デフォルトの見積もり時間（分）")
    task_category: str = Field(..., description="タスクの分類カテゴリ (例: 企画, 編集, 宣伝)")
    
    model_config = ConfigDict(from_attributes=True)

class TaskTemplateCreate(TaskTemplateBase):
    """新規作成用スキーマ (現状、Baseと同じ)"""
    pass

class TaskTemplate(TaskTemplateBase):
    """DBからの読み取り・レスポンス用スキーマ"""
    task_template_id: int