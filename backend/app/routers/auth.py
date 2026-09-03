from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models.auth import User
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.rbac import get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, RoleSwitchRequest, UserCreate

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_deleted == False).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = create_access_token(subject=user.id, role=user.role, org_id=user.organization_id)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

@router.get("/users", response_model=List[UserResponse])
def list_demo_users(db: Session = Depends(get_db)):
    """Returns available users across all roles for quick demo switching in UI."""
    users = db.query(User).filter(User.is_deleted == False).all()
    return [UserResponse.model_validate(u) for u in users]

@router.post("/switch-role", response_model=TokenResponse)
def switch_role(payload: RoleSwitchRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Demo helper: switch active role for current user session without needing to re-login."""
    valid_roles = ["Admin", "Sustainability Manager", "ESG Analyst", "Auditor", "Supplier", "C-Suite"]
    if payload.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of {valid_roles}")
    
    current_user.role = payload.role
    db.commit()
    db.refresh(current_user)
    
    access_token = create_access_token(subject=current_user.id, role=current_user.role, org_id=current_user.organization_id)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(current_user)
    )
