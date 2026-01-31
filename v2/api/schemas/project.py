from pydantic import BaseModel
from datetime import date

class ProjectCreate(BaseModel):
    theme: str
    due_date: date | None = None

class ProjectOut(BaseModel):
    project_id: int
    theme: str
    due_date: date | None
    progress_rate: float

    class Config:
        from_attributes = True

class ProjectDetailOut(BaseModel):
    project_id: int
    theme: str
    due_date: date | None
    publish_scheduled_at: date | None = None
    memo: str | None = None

    class Config:
        from_attributes = True