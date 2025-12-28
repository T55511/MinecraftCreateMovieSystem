# app/models/master.py

from sqlalchemy import Column, Integer, String, Boolean, Text, ARRAY, ForeignKey # type: ignore
from ..database import Base

# m_status モデル (t_project が参照)
class DBStatus(Base):
    __tablename__ = 'm_status'
    status_id = Column(Integer, primary_key=True)
    status_name = Column(String(50), nullable=False)
    # ... 他のカラムは省略 ...

# m_personal_angle モデル (t_project が参照)
class DBAngle(Base):
    __tablename__ = 'm_personal_angle'
    angle_id = Column(Integer, primary_key=True)
    angle_name = Column(String(50), nullable=False)
    prompt_instruction = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    # ... 他のカラムは省略 ...

# m_task_template モデル (t_project_task が参照)
class DBTaskTemplate(Base):
    __tablename__ = 'm_task_template'
    task_template_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_name = Column(String(100), nullable=False)
    est_time_min = Column(Integer, nullable=False)
    is_timer_target = Column(Boolean, nullable=False, default=False)
    default_status = Column(String(20), nullable=False, default='未着手')
    task_category = Column(String(50), nullable=False)
    # ... 他のカラムは省略 ...

# m_transition_rule モデル
class DBTransitionRule(Base):
    __tablename__ = 'm_transition_rule'
    rule_id = Column(Integer, primary_key=True)
    current_status_id = Column(Integer, ForeignKey('m_status.status_id'), nullable=False)
    next_status_id = Column(Integer, ForeignKey('m_status.status_id'), nullable=False)
    required_task_ids = Column(ARRAY(Integer), nullable=False) # 必要な完了済みタスクIDのリスト
    is_active = Column(Boolean, nullable=False, default=True)