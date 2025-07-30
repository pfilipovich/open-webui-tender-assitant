from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from open_webui.models.checklists import (
    Checklists,
    ChecklistModel,
    ChecklistUserResponse,
    ChecklistForm
)
from open_webui.models.prompts import Prompts
from open_webui.utils.auth import get_current_user, get_admin_user
from open_webui.models.users import User
from pydantic import BaseModel

router = APIRouter()

class ChecklistItemResult(BaseModel):
    prompt_command: str
    prompt_title: Optional[str] = None
    prompt_content: Optional[str] = None
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    structured_output: bool = False
    structured_output_schema: Optional[str] = None

class ChecklistExecutionResult(BaseModel):
    checklist_command: str
    checklist_title: str
    success: bool
    items: List[ChecklistItemResult]
    total_items: int
    successful_items: int
    failed_items: int

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

############################
# ExecuteChecklistByCommand
############################

@router.post("/command/{command}/execute", response_model=ChecklistExecutionResult)
async def execute_checklist_by_command(command: str, user=Depends(get_current_user)):
    # Get the checklist
    checklist = Checklists.get_checklist_by_command(command)
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist not found"
        )
    
    # Check permissions (for now, allow anyone to execute - can be restricted later)
    # TODO: Add access control for checklist execution
    
    # Execute each item in the checklist
    results = []
    successful_count = 0
    failed_count = 0
    
    for item in sorted(checklist.items, key=lambda x: x.order_index):
        item_result = ChecklistItemResult(
            prompt_command=item.prompt_command,
            success=False
        )
        
        try:
            # Get the prompt referenced by this checklist item
            prompt = Prompts.get_prompt_by_command(item.prompt_command)
            if not prompt:
                item_result.error = f"Prompt '{item.prompt_command}' not found"
                failed_count += 1
            else:
                # Set prompt details
                item_result.prompt_title = prompt.title
                item_result.prompt_content = prompt.content
                item_result.structured_output = prompt.structured_output or False
                item_result.structured_output_schema = prompt.structured_output_schema
                
                # For now, just return the prompt content as the result
                # In a full implementation, this would execute the prompt against an LLM
                item_result.result = f"Prompt '{prompt.title}' ready for execution: {prompt.content}"
                item_result.success = True
                successful_count += 1
                
        except Exception as e:
            item_result.error = f"Error processing item: {str(e)}"
            failed_count += 1
        
        results.append(item_result)
    
    return ChecklistExecutionResult(
        checklist_command=checklist.command,
        checklist_title=checklist.title,
        success=successful_count > 0,
        items=results,
        total_items=len(results),
        successful_items=successful_count,
        failed_items=failed_count
    )