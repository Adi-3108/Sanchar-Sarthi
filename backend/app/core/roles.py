from __future__ import annotations

PUBLIC_ROLES = {"guest", "citizen"}
CONTROL_ROLES = {"control_room_officer", "control_room", "police_officer"}
ADMIN_ROLES = {"admin"}

ROLE_ALIASES = {
    "public_viewer": "guest",
    "control_room": "control_room_officer",
    "police_officer": "control_room_officer",
}


def canonical_role(role: str | None) -> str:
    value = (role or "guest").strip()
    return ROLE_ALIASES.get(value, value)


def role_allowed(actual_role: str | None, allowed_roles: tuple[str, ...]) -> bool:
    actual = canonical_role(actual_role)
    allowed = {canonical_role(role) for role in allowed_roles}
    return actual in allowed
