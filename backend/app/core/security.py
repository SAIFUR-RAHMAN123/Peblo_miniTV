"""
Role auth: static bearer tokens -> role, checked server-side.

The CMS sends `Authorization: Bearer <key>`. Which role that key maps to is
looked up here, not trusted from anything the client asserts -- there is no
`role` field the client can set. Swapping this for JWT/OAuth later only
touches this file: `require_role` stays the same shape.
"""
from enum import Enum

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings


class Role(str, Enum):
    EDITOR = "editor"
    ADMIN = "admin"


def get_current_role(authorization: str | None = Header(default=None)) -> Role:
    settings = get_settings()
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected: Bearer <api-key>",
        )
    token = authorization.split(" ", 1)[1].strip()
    if token == settings.admin_api_key:
        return Role.ADMIN
    if token == settings.editor_api_key:
        return Role.EDITOR
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")


def require_role(*allowed: Role):
    def _checker(role: Role = Depends(get_current_role)) -> Role:
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role.value}' is not permitted to perform this action. "
                       f"Requires one of: {', '.join(r.value for r in allowed)}.",
            )
        return role
    return _checker


require_editor = require_role(Role.EDITOR, Role.ADMIN)
require_admin = require_role(Role.ADMIN)