from enum import Enum
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.security import decode_access_token
from app.models.auth import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

class Role(str, Enum):
    ADMIN = "Admin"
    SUSTAINABILITY_MANAGER = "Sustainability Manager"
    ESG_ANALYST = "ESG Analyst"
    AUDITOR = "Auditor"
    SUPPLIER = "Supplier"
    C_SUITE = "C-Suite"

# Permission matrices
READ_ONLY_ROLES = [Role.C_SUITE, Role.AUDITOR]
EDIT_ROLES = [Role.ADMIN, Role.SUSTAINABILITY_MANAGER, Role.ESG_ANALYST]
ADMIN_ONLY = [Role.ADMIN]

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        # Check if running in development mode and allow a default user fallback if authorization header missing
        # but raise 401 if token is present and invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    # Respect temporary demo session role from JWT claims in memory (non-mutating)
    token_role = payload.get("role")
    if token_role:
        user.role = token_role

    return user

def require_roles(allowed_roles: List[Role | str]):
    """FastAPI Dependency checking whether current user's role is in allowed_roles."""
    role_values = [r.value if isinstance(r, Role) else r for r in allowed_roles]

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action forbidden for role '{current_user.role}'. Required one of: {role_values}",
            )
        return current_user

    return role_checker

def verify_facility_access(current_user: User, facility_id: str) -> bool:
    """Verifies tenant/facility segregation using least-privilege principles."""
    if current_user.role in [Role.ADMIN.value, Role.SUSTAINABILITY_MANAGER.value]:
        return True
    
    # Scoped roles (Supplier, Auditor) with empty permissions get zero facility access
    if current_user.role in [Role.SUPPLIER.value, Role.AUDITOR.value]:
        if not current_user.facility_permissions:
            return False
        return facility_id in current_user.facility_permissions

    # Internal Analysts with empty permissions have org-wide facility access
    if not current_user.facility_permissions:
        return True
    return facility_id in current_user.facility_permissions

def require_facility_access(current_user: User, facility_id: str):
    """Enforces facility-level security boundary, raising 403 if unauthorized."""
    if not verify_facility_access(current_user, facility_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User '{current_user.email}' lacks permission for facility '{facility_id}'"
        )
