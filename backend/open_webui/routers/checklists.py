from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request

from open_webui.models.checklists import (
    Checklists,
    ChecklistForm,
    ChecklistModel,
    ChecklistUserResponse,
)
from open_webui.models.users import Users, UserResponse
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.auth import get_verified_user
from open_webui.utils.access_control import has_access, has_permission

router = APIRouter()


@router.get("/", response_model=list[ChecklistUserResponse])
async def get_checklists(user=Depends(get_verified_user)):
    if user.role == "admin":
        checklists = Checklists.get_checklists()
    else:
        checklists = Checklists.get_checklists_by_user_id(user.id, "read")

    return [
        ChecklistUserResponse(
            **{
                **c.model_dump(),
                "user": UserResponse(**Users.get_user_by_id(c.user_id).model_dump()),
            }
        )
        for c in checklists
    ]


@router.get("/list", response_model=list[ChecklistUserResponse])
async def get_checklist_list(user=Depends(get_verified_user)):
    if user.role == "admin":
        checklists = Checklists.get_checklists()
    else:
        checklists = Checklists.get_checklists_by_user_id(user.id, "write")

    return [
        ChecklistUserResponse(
            **{
                **c.model_dump(),
                "user": UserResponse(**Users.get_user_by_id(c.user_id).model_dump()),
            }
        )
        for c in checklists
    ]


@router.post("/create", response_model=Optional[ChecklistModel])
async def create_new_checklist(
    request: Request, form_data: ChecklistForm, user=Depends(get_verified_user)
):
    if user.role != "admin" and not has_permission(
        user.id, "workspace.checklists", request.app.state.config.USER_PERMISSIONS
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    checklist = Checklists.insert_new_checklist(user.id, form_data)
    if checklist:
        return checklist
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.DEFAULT(),
    )


@router.get("/{id}", response_model=Optional[ChecklistModel])
async def get_checklist_by_id(id: str, user=Depends(get_verified_user)):
    checklist = Checklists.get_checklist_by_id(id)
    if checklist and (
        user.role == "admin"
        or checklist.user_id == user.id
        or has_access(user.id, "read", checklist.access_control)
    ):
        return checklist
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ERROR_MESSAGES.NOT_FOUND,
    )


@router.post("/{id}/update", response_model=Optional[ChecklistModel])
async def update_checklist_by_id(
    id: str, form_data: ChecklistForm, user=Depends(get_verified_user)
):
    checklist = Checklists.get_checklist_by_id(id)
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        checklist.user_id != user.id
        and not has_access(user.id, "write", checklist.access_control)
        and user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    updated = Checklists.update_checklist_by_id(id, form_data)
    if updated:
        return updated
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.DEFAULT(),
    )


@router.delete("/{id}/delete", response_model=bool)
async def delete_checklist_by_id(id: str, user=Depends(get_verified_user)):
    checklist = Checklists.get_checklist_by_id(id)
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        checklist.user_id != user.id
        and not has_access(user.id, "write", checklist.access_control)
        and user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    result = Checklists.delete_checklist_by_id(id)
    return result
