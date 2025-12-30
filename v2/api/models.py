from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from db import Base


class MPhase(Base):
    __tablename__ = "m_phase"

    phase_id = Column(Integer, primary_key=True, index=True)
    phase_key = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class MTaskTemplate(Base):
    __tablename__ = "m_task_template"

    task_template_id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(200), nullable=False)
    phase_id = Column(Integer, ForeignKey("m_phase.phase_id"), nullable=False)
    est_time_min = Column(Integer, nullable=False, default=0)
    is_timer_target = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    phase = relationship("MPhase")


class MCheckItem(Base):
    __tablename__ = "m_check_item"

    check_item_id = Column(Integer, primary_key=True, index=True)
    label = Column(String(200), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)


class MTaskCheckMap(Base):
    __tablename__ = "m_task_check_map"

    task_template_id = Column(Integer, ForeignKey("m_task_template.task_template_id"), primary_key=True)
    check_item_id = Column(Integer, ForeignKey("m_check_item.check_item_id"), primary_key=True)


class TProject(Base):
    __tablename__ = "t_project"

    project_id = Column(Integer, primary_key=True, index=True)
    theme = Column(String(300), nullable=False)
    due_date = Column(Date, nullable=True)
    publish_scheduled_at = Column(Date, nullable=True)
    progress_rate = Column(Float, nullable=False, default=0.0)

    # v2最初は status/progress は後回しでOK（必要になったら追加）
    memo = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TProjectTask(Base):
    __tablename__ = "t_project_task"

    project_task_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("t_project.project_id"), nullable=False, index=True)
    task_template_id = Column(Integer, ForeignKey("m_task_template.task_template_id"), nullable=False)

    # スナップショット（テンプレ変更で過去が壊れない）
    task_name_snapshot = Column(String(200), nullable=False)
    phase_id_snapshot = Column(Integer, nullable=False)

    status = Column(String(20), nullable=False, default="未着手")  # 未着手/進行中/完了
    est_time_min_snapshot = Column(Integer, nullable=False, default=0)
    actual_time_min = Column(Float, nullable=False, default=0.0)

    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("project_id", "task_template_id", name="uq_project_task_template"),
    )

class TTimerLog(Base):
    __tablename__ = "t_timer_log"

    timer_log_id = Column(Integer, primary_key=True, autoincrement=True)
    project_task_id = Column(Integer, ForeignKey("t_project_task.project_task_id"), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_min = Column(Float, nullable=True)