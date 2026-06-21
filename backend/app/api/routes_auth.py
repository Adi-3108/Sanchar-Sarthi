from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import AuthContext, get_auth_context

router = APIRouter(prefix="/api/auth", tags=["auth"])

class AuthMeResponse(BaseModel):
    role: str
    email: str | None = None
    firebase_uid: str

@router.get("/me", response_model=AuthMeResponse)
def get_me(auth: AuthContext = Depends(get_auth_context)) -> AuthMeResponse:
    """
    Returns the authenticated user's role and details based on their Firebase token.
    This ensures that the client apps use the backend-enforced role, not a UI-selected role.
    """
    return AuthMeResponse(
        role=auth.role,
        email=auth.email,
        firebase_uid=auth.firebase_uid,
    )
