from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from open_webui.models.checklists import (
    Checklists,
    ChecklistModel,
    ChecklistUserResponse,
    ChecklistForm
)
from open_webui.utils.auth import get_current_user, get_admin_user
from open_webui.models.users import User

router = APIRouter()

############################
# GetChecklists
############################

@router.get("/", response_model=List[ChecklistUserResponse])
async def get_checklists(user=Depends(get_current_user)):
    if user.role == "admin":
        return Checklists.get_checklists()
    else:
        return Checklists.get_checklists_by_user_id(user.id, "read")

############################
# GetChecklistList (for editing)
############################

@router.get("/list", response_model=List[ChecklistUserResponse])
async def get_checklist_list(user=Depends(get_current_user)):
    if user.role == "admin":
        return Checklists.get_checklists()
    else:
        return Checklists.get_checklists_by_user_id(user.id, "write")

############################
# CreateNewChecklist
############################

@router.post("/create", response_model=ChecklistModel)
async def create_new_checklist(form_data: ChecklistForm, user=Depends(get_current_user)):
    # Validate command doesn't exist
    existing = Checklists.get_checklist_by_command(form_data.command)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checklist with this command already exists"
        )
    
    checklist = Checklists.insert_new_checklist(user.id, form_data)
    if checklist:
        return checklist
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create checklist"
        )

############################
# GetChecklistByCommand
############################

@router.get("/command/{command}", response_model=ChecklistModel)
async def get_checklist_by_command(command: str):
    checklist = Checklists.get_checklist_by_command(command)
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist not found"
        )
    return checklist

############################
# UpdateChecklistByCommand
############################

@router.post("/command/{command}/update", response_model=ChecklistModel)
async def update_checklist_by_command(
    command: str, form_data: ChecklistForm, user=Depends(get_current_user)
):
    existing = Checklists.get_checklist_by_command(command)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist not found"
        )
    
    # Check permissions (owner or admin)
    if existing.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    updated_checklist = Checklists.update_checklist_by_command(command, form_data)
    if updated_checklist:
        return updated_checklist
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update checklist"
        )

############################
# DeleteChecklistByCommand
############################

@router.delete("/command/{command}/delete", response_model=bool)
async def delete_checklist_by_command(command: str, user=Depends(get_current_user)):
    existing = Checklists.get_checklist_by_command(command)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist not found"
        )
    
    # Check permissions (owner or admin)
    if existing.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    success = Checklists.delete_checklist_by_command(command)
    if success:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete checklist"
        )