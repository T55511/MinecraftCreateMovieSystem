from __future__ import annotations

import uuid
from datetime import datetime

from db import Base
from sqlalchemy import (  # type: ignore
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID  # type: ignore
from sqlalchemy.orm import Mapped, mapped_column, relationship  # type: ignore
from sqlalchemy.sql import func  # type: ignore


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

    # ✅ 追加：SQL側に合わせる
    default_status = Column(String(20), nullable=False, server_default="未着手")
    task_category = Column(String(50), nullable=False, server_default="GENERAL")

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

    task_template_id = Column(
        Integer, ForeignKey("m_task_template.task_template_id"), primary_key=True
    )
    check_item_id = Column(
        Integer, ForeignKey("m_check_item.check_item_id"), primary_key=True
    )


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
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TProjectTask(Base):
    __tablename__ = "t_project_task"

    project_task_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, ForeignKey("t_project.project_id"), nullable=False, index=True
    )
    task_template_id = Column(
        Integer, ForeignKey("m_task_template.task_template_id"), nullable=False
    )

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
        UniqueConstraint(
            "project_id", "task_template_id", name="uq_project_task_template"
        ),
    )


class TTimerLog(Base):
    __tablename__ = "t_timer_log"

    timer_log_id = Column(Integer, primary_key=True, autoincrement=True)
    project_task_id = Column(
        Integer, ForeignKey("t_project_task.project_task_id"), nullable=False
    )

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_min = Column(Float, nullable=True)


# -------------------------
# Status definition
# -------------------------
class MstStatusDefinition(Base):
    __tablename__ = "mst_status_definition"
    status_key = Column(String, primary_key=True)  # immutable at app layer
    display_name = Column(Text, nullable=False)
    scope = Column(String, nullable=False)
    is_done = Column(Boolean, nullable=False, server_default="false")
    color_hex = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "scope IN ('PROJECT','SUBTASK','COMMON')", name="ck_status_definition_scope"
        ),
        Index("idx_mst_status_definition_scope", "scope"),
    )


class MstStatusUI(Base):
    __tablename__ = "mst_status_ui"
    scope = Column(String, nullable=False)
    status_key = Column(
        String, ForeignKey("mst_status_definition.status_key"), nullable=False
    )
    display_order = Column(Integer, nullable=False)
    is_visible = Column(Boolean, nullable=False, server_default="true")

    __table_args__ = (
        PrimaryKeyConstraint("scope", "status_key", name="pk_mst_status_ui"),
        CheckConstraint(
            "scope IN ('PROJECT','SUBTASK','COMMON')", name="ck_status_ui_scope"
        ),
        Index("idx_mst_status_ui_scope_order", "scope", "display_order"),
    )


# -------------------------
# Checklist template (no versioning)
# -------------------------
class TplCheckitem(Base):
    __tablename__ = "tpl_checkitem"
    checkitem_id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    default_checked = Column(
        Boolean, nullable=False, server_default="true"
    )  # default ON
    importance = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("idx_tpl_checkitem_active", "is_active"),)


# -------------------------
# Subtask template (versioned)
# -------------------------
class TplSubtaskTemplate(Base):
    __tablename__ = "tpl_subtask_template"
    subtask_template_id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    latest_version = Column(Integer, nullable=False, server_default="1")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("idx_tpl_subtask_template_active", "is_active"),)


class TplSubtaskTemplateVersion(Base):
    __tablename__ = "tpl_subtask_template_version"
    subtask_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tpl_subtask_template.subtask_template_id"),
        nullable=False,
    )
    version = Column(Integer, nullable=False)
    snapshot = Column(JSONB, nullable=False)
    change_note = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by = Column(Text, nullable=False, server_default="local-user")

    __table_args__ = (
        PrimaryKeyConstraint(
            "subtask_template_id", "version", name="pk_tpl_subtask_template_version"
        ),
        CheckConstraint("version >= 1", name="ck_subtask_template_version_ge_1"),
    )


# -------------------------
# Estimate master (minutes)
# -------------------------
class MstEstimateMaster(Base):
    __tablename__ = "mst_estimate_master"
    estimate_id = Column(UUID(as_uuid=True), primary_key=True)
    subtask_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tpl_subtask_template.subtask_template_id"),
        nullable=False,
    )
    minutes = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("minutes >= 0", name="ck_estimate_minutes_ge_0"),
        Index("idx_mst_estimate_master_subtask", "subtask_template_id"),
    )


# -------------------------
# Project template (versioned)
# -------------------------
class TplProjectTemplate(Base):
    __tablename__ = "tpl_project_template"
    project_template_id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    initial_status_key = Column(
        String, ForeignKey("mst_status_definition.status_key"), nullable=False
    )
    default_angle_key = Column(String, nullable=True)  # FK later if needed
    is_active = Column(Boolean, nullable=False, server_default="true")
    latest_version = Column(Integer, nullable=False, server_default="1")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("idx_tpl_project_template_active", "is_active"),)


class TplProjectTemplateVersion(Base):
    __tablename__ = "tpl_project_template_version"
    project_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tpl_project_template.project_template_id"),
        nullable=False,
    )
    version = Column(Integer, nullable=False)
    snapshot = Column(JSONB, nullable=False)
    change_note = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by = Column(Text, nullable=False, server_default="local-user")

    __table_args__ = (
        PrimaryKeyConstraint(
            "project_template_id", "version", name="pk_tpl_project_template_version"
        ),
        CheckConstraint("version >= 1", name="ck_project_template_version_ge_1"),
    )


# -------------------------
# Angle master
# -------------------------
class MstAngle(Base):
    __tablename__ = "mst_angle"
    angle_key = Column(String, primary_key=True)
    display_name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    recommended_seconds = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TCheckResult(Base):
    __tablename__ = "t_check_result"

    project_task_id = Column(
        Integer, ForeignKey("t_project_task.project_task_id"), primary_key=True
    )
    check_item_id = Column(
        Integer, ForeignKey("m_check_item.check_item_id"), primary_key=True
    )
    is_checked = Column(Boolean, nullable=False, default=False)


class TEventLog(Base):
    __tablename__ = "t_event_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ここを UUID に
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    event_type: Mapped[str] = mapped_column(String(16), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(128), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


Index("ix_event_log_ts", TEventLog.timestamp.desc())
Index("ix_event_log_level_ts", TEventLog.level, TEventLog.timestamp.desc())
Index("ix_event_log_type_ts", TEventLog.event_type, TEventLog.timestamp.desc())
Index("ix_event_log_reqid", TEventLog.request_id)
Index("ix_event_log_action", TEventLog.action)
Index("ix_event_log_target", TEventLog.target_type, TEventLog.target_id)
