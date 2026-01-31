from pydantic import BaseModel

class ProjectTaskOut(BaseModel):
    project_task_id: int
    project_id: int
    task_template_id: int
    task_name: str
    status: str
    est_time_min: int
    actual_time_min: float
    sort_order: int
    is_active: bool

class TaskStatusPatch(BaseModel):
    status: str

class ChecklistItemOut(BaseModel):
    check_item_id: int
    label: str
    is_checked: bool

class ChecklistUpdateItem(BaseModel):
    check_item_id: int
    is_checked: bool