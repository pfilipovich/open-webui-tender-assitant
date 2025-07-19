import time
from typing import Optional, List
from open_webui.internal.db import Base, get_db
from open_webui.models.users import Users, UserResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from open_webui.utils.access_control import has_access

####################
# Checklists DB Schema
####################

class Checklist(Base):
    __tablename__ = "checklist"
    
    id = Column(String, primary_key=True)
    command = Column(String, unique=True, nullable=False)
    user_id = Column(String, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    timestamp = Column(BigInteger, nullable=False)
    access_control = Column(JSON, nullable=True)
    
    # Relationship to items
    items = relationship("ChecklistItem", back_populates="checklist", cascade="all, delete-orphan")

class ChecklistItem(Base):
    __tablename__ = "checklist_item"
    
    id = Column(String, primary_key=True)
    checklist_id = Column(String, ForeignKey("checklist.id"), nullable=False)
    prompt_command = Column(String, nullable=False)  # References prompt.command
    order_index = Column(Integer, nullable=False)
    settings = Column(JSON, nullable=True)  # Per-item settings
    
    # Relationship back to checklist
    checklist = relationship("Checklist", back_populates="items")

####################
# Pydantic Models
####################

class ChecklistItemModel(BaseModel):
    id: str
    checklist_id: str
    prompt_command: str
    order_index: int
    settings: Optional[dict] = None
    model_config = ConfigDict(from_attributes=True)

class ChecklistModel(BaseModel):
    id: str
    command: str
    user_id: str
    title: str
    description: Optional[str] = None
    timestamp: int
    access_control: Optional[dict] = None
    items: List[ChecklistItemModel] = []
    model_config = ConfigDict(from_attributes=True)

class ChecklistUserResponse(ChecklistModel):
    user: Optional[UserResponse] = None

class ChecklistForm(BaseModel):
    command: str
    title: str
    description: Optional[str] = None
    access_control: Optional[dict] = None
    items: List[dict] = []  # [{prompt_command: str, order_index: int, settings: dict}]

####################
# Database Operations
####################

class ChecklistsTable:
    def insert_new_checklist(self, user_id: str, form_data: ChecklistForm) -> Optional[ChecklistModel]:
        import uuid
        checklist_id = str(uuid.uuid4())
        
        checklist = ChecklistModel(
            id=checklist_id,
            user_id=user_id,
            **form_data.model_dump(exclude={"items"}),
            timestamp=int(time.time()),
            items=[]
        )
        
        try:
            with get_db() as db:
                # Create checklist
                result = Checklist(**checklist.model_dump(exclude={"items"}))
                db.add(result)
                db.flush()  # Get the ID
                
                # Create items
                for item_data in form_data.items:
                    item = ChecklistItem(
                        id=str(uuid.uuid4()),
                        checklist_id=checklist_id,
                        **item_data
                    )
                    db.add(item)
                
                db.commit()
                return self.get_checklist_by_command(form_data.command)
        except Exception as e:
            print(f"Error creating checklist: {e}")
            return None
    
    def get_checklist_by_command(self, command: str) -> Optional[ChecklistModel]:
        try:
            with get_db() as db:
                checklist = db.query(Checklist).filter_by(command=command).first()
                if not checklist:
                    return None
                
                items = db.query(ChecklistItem).filter_by(checklist_id=checklist.id).order_by(ChecklistItem.order_index).all()
                
                checklist_data = ChecklistModel.model_validate(checklist)
                checklist_data.items = [ChecklistItemModel.model_validate(item) for item in items]
                
                return checklist_data
        except Exception as e:
            print(f"Error getting checklist: {e}")
            return None
    
    def get_checklists(self) -> List[ChecklistUserResponse]:
        with get_db() as db:
            checklists = []
            for checklist in db.query(Checklist).order_by(Checklist.timestamp.desc()).all():
                user = Users.get_user_by_id(checklist.user_id)
                items = db.query(ChecklistItem).filter_by(checklist_id=checklist.id).order_by(ChecklistItem.order_index).all()
                
                checklist_data = ChecklistModel.model_validate(checklist)
                checklist_data.items = [ChecklistItemModel.model_validate(item) for item in items]
                
                checklists.append(
                    ChecklistUserResponse.model_validate({
                        **checklist_data.model_dump(),
                        "user": user.model_dump() if user else None,
                    })
                )
            return checklists
    
    def get_checklists_by_user_id(self, user_id: str, permission: str = "write") -> List[ChecklistUserResponse]:
        checklists = self.get_checklists()
        return [
            checklist for checklist in checklists
            if checklist.user_id == user_id or has_access(user_id, permission, checklist.access_control)
        ]
    
    def update_checklist_by_command(self, command: str, form_data: ChecklistForm) -> Optional[ChecklistModel]:
        try:
            with get_db() as db:
                checklist = db.query(Checklist).filter_by(command=command).first()
                if not checklist:
                    return None
                
                # Update checklist
                checklist.title = form_data.title
                checklist.description = form_data.description
                checklist.access_control = form_data.access_control
                checklist.timestamp = int(time.time())
                
                # Delete existing items
                db.query(ChecklistItem).filter_by(checklist_id=checklist.id).delete()
                
                # Create new items
                import uuid
                for item_data in form_data.items:
                    item = ChecklistItem(
                        id=str(uuid.uuid4()),
                        checklist_id=checklist.id,
                        **item_data
                    )
                    db.add(item)
                
                db.commit()
                return self.get_checklist_by_command(command)
        except Exception as e:
            print(f"Error updating checklist: {e}")
            return None
    
    def delete_checklist_by_command(self, command: str) -> bool:
        try:
            with get_db() as db:
                checklist = db.query(Checklist).filter_by(command=command).first()
                if checklist:
                    db.query(ChecklistItem).filter_by(checklist_id=checklist.id).delete()
                    db.query(Checklist).filter_by(command=command).delete()
                    db.commit()
                return True
        except Exception:
            return False

Checklists = ChecklistsTable()