from pydantic import BaseModel, Field
from typing import Optional


# ---------- Schemas ----------
class MstStatusDefinitionCreate(BaseModel):
    status_key: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=200)
    scope: str = Field(..., pattern=r"^(PROJECT|SUBTASK|COMMON)$")
    is_done: bool = False
    color_hex: Optional[str] = None
    is_active: bool = True


class MstStatusDefinitionUpdate(BaseModel):
    # status_key は更新不可なので含めない
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    scope: Optional[str] = Field(default=None, pattern=r"^(PROJECT|SUBTASK|COMMON)$")  # 変更を許可するかどうかは運用次第。嫌なら削除OK。
    is_done: Optional[bool] = None
    color_hex: Optional[str] = None
    is_active: Optional[bool] = None


class MstStatusDefinitionOut(BaseModel):
    status_key: str
    display_name: str
    scope: str
    is_done: bool
    color_hex: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class MstStatusUIItemIn(BaseModel):
    status_key: str
    display_order: int = Field(..., ge=0)
    is_visible: bool = True


class MstStatusUIItemOut(BaseModel):
    scope: str
    status_key: str
    display_order: int
    is_visible: bool

    class Config:
        from_attributes = True