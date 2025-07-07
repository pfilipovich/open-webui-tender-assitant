import time
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, Text, JSON

from open_webui.internal.db import Base, get_db
from open_webui.models.users import Users, UserResponse
from open_webui.utils.access_control import has_access


class Checklist(Base):
    __tablename__ = "checklist"

    id = Column(Text, primary_key=True)
    user_id = Column(Text)

    title = Column(Text)
    items = Column(JSON, nullable=True)

    access_control = Column(JSON, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class ChecklistModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    items: Optional[list[dict]] = None
    access_control: Optional[dict] = None
    created_at: int
    updated_at: int


class ChecklistForm(BaseModel):
    title: str
    items: Optional[list[dict]] = None
    access_control: Optional[dict] = None


class ChecklistUserResponse(ChecklistModel):
    user: Optional[UserResponse] = None


class ChecklistTable:
    def insert_new_checklist(self, user_id: str, form_data: ChecklistForm) -> Optional[ChecklistModel]:
        with get_db() as db:
            checklist = ChecklistModel(
                **{
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    **form_data.model_dump(),
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            new_checklist = Checklist(**checklist.model_dump())
            db.add(new_checklist)
            db.commit()
            return checklist

    def get_checklists(self) -> list[ChecklistModel]:
        with get_db() as db:
            checklists = db.query(Checklist).order_by(Checklist.updated_at.desc()).all()
            return [ChecklistModel.model_validate(c) for c in checklists]

    def get_checklists_by_user_id(self, user_id: str, permission: str = "write") -> list[ChecklistModel]:
        checklists = self.get_checklists()
        return [
            c
            for c in checklists
            if c.user_id == user_id or has_access(user_id, permission, c.access_control)
        ]

    def get_checklist_by_id(self, id: str) -> Optional[ChecklistModel]:
        with get_db() as db:
            checklist = db.query(Checklist).filter(Checklist.id == id).first()
            return ChecklistModel.model_validate(checklist) if checklist else None

    def update_checklist_by_id(self, id: str, form_data: ChecklistForm) -> Optional[ChecklistModel]:
        with get_db() as db:
            checklist = db.query(Checklist).filter(Checklist.id == id).first()
            if not checklist:
                return None

            checklist.title = form_data.title
            checklist.items = form_data.items
            checklist.access_control = form_data.access_control
            checklist.updated_at = int(time.time())

            db.commit()
            return ChecklistModel.model_validate(checklist)

    def delete_checklist_by_id(self, id: str) -> bool:
        with get_db() as db:
            db.query(Checklist).filter(Checklist.id == id).delete()
            db.commit()
            return True


Checklists = ChecklistTable()
