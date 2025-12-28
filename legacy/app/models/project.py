# app/models/project.py

from sqlalchemy import Column, Integer, String, BigInteger, Text, Boolean, DateTime, ForeignKey, ARRAY, JSON, func, Float # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from datetime import datetime
from ..database import Base  # app/database.py で定義したBaseをインポート

# --- 追加: 参照先のマスタモデルをインポートする ---
# このインポートにより、SQLAlchemyのBaseにマスタモデルの情報が読み込まれる
from .master import DBStatus, DBAngle, DBTaskTemplate 
# ----------------------------------------------------

# t_project テーブルに対応するモデル
class DBProject(Base):
    __tablename__ = 't_project'
    
    project_id = Column(BigInteger, primary_key=True, index=True)
    type_id = Column(Integer, nullable=False)
    current_status_id = Column(Integer, ForeignKey('m_status.status_id'), nullable=False)
    theme = Column(String(255), nullable=False)
    input_angle_id = Column(Integer, ForeignKey('m_personal_angle.angle_id'), nullable=False)
    scaffold_data = Column(JSON, nullable=False)  # JSONBとして扱います
    thumbnail_concept = Column(JSON)
    final_title = Column(String(255))
    final_description = Column(Text)
    summary_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    published_at = Column(DateTime)
    progress_rate = Column(Integer, nullable=False, default=0)
    
    # リレーションシップ定義（サブタスクを取得するために使用）
    tasks = relationship("DBProjectTask", back_populates="project")
    
# t_project_task テーブルに対応するモデル
class DBProjectTask(Base):
    __tablename__ = 't_project_task'  # 👈 これが必須です！
    
    project_task_id = Column(BigInteger, primary_key=True, index=True)
    project_id = Column(BigInteger, ForeignKey('t_project.project_id'), nullable=False)
    task_template_id = Column(Integer, ForeignKey('m_task_template.task_template_id'), nullable=False)
    est_time_min = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    actual_time_min = Column(Float, nullable=False, default=0)

    # リレーションシップ
    project = relationship("DBProject", back_populates="tasks")
    timer_logs = relationship("DBTimerLog", back_populates="task") # 👈 新しく追加したリレーション

# t_timer_log テーブルに対応するモデル
class DBTimerLog(Base):
    __tablename__ = 't_timer_log'
    
    log_id = Column(BigInteger, primary_key=True, index=True)
    # 外部キー: プロジェクトタスク
    project_task_id = Column(BigInteger, ForeignKey('t_project_task.project_task_id'), nullable=False) 
    start_time = Column(DateTime, nullable=False, default=func.now())
    end_time = Column(DateTime, nullable=True)
    duration_min = Column(Float, nullable=True) # 分単位で記録
    
    # リレーションシップ (DBProjectTask から参照可能)
    task = relationship("DBProjectTask", back_populates="timer_logs")