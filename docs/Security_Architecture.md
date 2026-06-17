# EventFlow AI Security Architecture

## 1. Security Scope

MVP is a hackathon prototype. It still must protect sensitive fields, avoid exposed database credentials, validate input, and prevent obvious abuse of citizen reports.

## 2. Authentication

MVP:

- Level 1 Admin / Control Room users log in with Firebase Auth email/password.
- Level 2 Registered Police Officer users log in with Firebase Auth email/password.
- Level 3 Public / Citizen access is open, rate-limited, validated, and restricted to public-safe information.

Future:

- Optional official BTP identity integration, SSO, or custom claims.
- Stronger production RBAC for admins, control room operators, registered police officers, public users, and judge/viewer accounts.

## 3. Authorization

MVP authorization model:

| Action | Access |
|---|---|
| View public advisories | Level 3 public |
| Submit citizen report | Level 3 public with rate limit |
| View officer-safe routing/diversion overlays | Level 2 registered police officer |
| Submit field update / confirm report | Level 2 registered police officer |
| View assigned event action plan | Level 2 registered police officer |
| View full command dashboard | Level 1 admin/control room |
| Add or deactivate police officers | Level 1 admin/control room |
| Load/upload dataset | Level 1 admin/control room |
| Reset demo scenario | Level 1 admin/control room |
| Generate internal post-event report | Level 1 admin/control room or assigned Level 2 officer based on deployment |

## 4. Firebase Auth And RBAC

MVP backend roles:

- `admin`
- `control_room`
- `police_officer`
- `public_viewer`

Human labels such as "Senior Planner", "Field Officer", "Citizen Reporter", or "Viewer/Judge" are UI/persona labels only. They must not be stored as backend authorization roles unless a future RBAC migration explicitly adds them.

Firebase Auth handles identity. EventFlow AI backend handles authorization.

MVP role source of truth:

| Concern | MVP Decision |
|---|---|
| Login provider | Firebase Auth email/password |
| Client credential | Firebase ID token |
| API header | `Authorization: Bearer <firebase_id_token>` |
| Backend verification | Firebase Admin SDK verifies ID token |
| Role source | `user_accounts.role` in PostgreSQL |
| Officer assignment source | `police_officer_profiles` and `officer_event_assignments` |
| Public access | No login required for public-safe endpoints |
| Phone OTP | Not in MVP to avoid SMS cost/verification complexity |

Implementation contract:

```python
from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException, status
import firebase_admin
from firebase_admin import auth as firebase_auth
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.orm.police_officer_profile import PoliceOfficerProfile
from app.orm.user_account import UserAccount

@dataclass(frozen=True)
class AuthContext:
    firebase_uid: str
    email: str | None
    role: str
    user_account_id: str
    officer_profile_id: str | None = None
    officer_id: str | None = None
    police_station: str | None = None
    assigned_corridors: list[str] | None = None
    assigned_zones: list[str] | None = None

def verify_firebase_token(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_FIREBASE_TOKEN"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not firebase_admin._apps:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "FIREBASE_NOT_CONFIGURED"})
    try:
        return firebase_auth.verify_id_token(token, check_revoked=True)
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "REVOKED_FIREBASE_TOKEN"})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_FIREBASE_TOKEN"})

def load_auth_context(db: Session, token_payload: dict) -> AuthContext:
    account = (
        db.query(UserAccount)
        .filter(UserAccount.auth_provider == "firebase")
        .filter(UserAccount.auth_provider_uid == token_payload["uid"])
        .first()
    )
    if not account or not account.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "INACTIVE_ACCOUNT"})

    officer_profile = None
    if account.role == "police_officer":
        officer_profile = (
            db.query(PoliceOfficerProfile)
            .filter(PoliceOfficerProfile.user_account_id == account.id)
            .filter(PoliceOfficerProfile.active.is_(True))
            .first()
        )
        if not officer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "OFFICER_PROFILE_REQUIRED"})

    return AuthContext(
        firebase_uid=token_payload["uid"],
        email=token_payload.get("email"),
        role=account.role,
        user_account_id=str(account.id),
        officer_profile_id=str(officer_profile.id) if officer_profile else None,
        officer_id=officer_profile.officer_id if officer_profile else None,
        police_station=officer_profile.police_station if officer_profile else None,
        assigned_corridors=officer_profile.assigned_corridors_json if officer_profile else None,
        assigned_zones=officer_profile.assigned_zones_json if officer_profile else None,
    )

def require_role(*allowed_roles: str):
    def dependency(
        token_payload: dict = Depends(verify_firebase_token),
        db: Session = Depends(get_db),
    ) -> AuthContext:
        context = load_auth_context(db, token_payload)
        if context.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "FORBIDDEN_ROLE"})
        return context
    return dependency
```

Full implementation details, including Firebase Admin initialization and frontend login helpers, are defined in `docs/Firebase_Auth_Implementation.md`.

Rules:

- Do not trust Firebase login alone for permissions; always check EventFlow role and officer assignment in backend.
- Do not use phone OTP in MVP unless a free verified setup is available.
- Do not expose Firebase Admin SDK service account secrets in frontend.
- Public Firebase config values may exist in frontend, but service account/private key values must be backend-only.

## 5. Officer Access MVP

Registered police officer access is implemented through Firebase Auth accounts created/registered by Level 1 Admin / Control Room.

Minimum officer fields:

- Firebase UID
- official/demo email
- `officer_id`
- display name
- rank/designation
- police station
- corridor/zone assignment
- active/inactive status

Officer authorization rules:

- Officers can view only assigned events, corridors, stations, and officer-safe overlays.
- Officers can submit field updates and confirm/deny citizen reports.
- Officers cannot upload datasets, reset demo data, add officers, or view sensitive internal admin settings.
- Officer portal must hide public-sensitive internals such as exact control-room strategy if not assigned.

## 6. Public Access MVP

Public/citizen access is open but constrained:

- Public users can submit reports and view public advisories.
- Public users cannot see exact manpower deployment, officer identities, internal confidence ledgers, raw ASTraM sensitive fields, or admin-only data.
- Public reports remain unverified until confidence scoring and/or officer confirmation.

## 7. Session Strategy

MVP:

- Firebase Auth client SDK manages browser session.
- Frontend sends Firebase ID token to FastAPI as `Authorization: Bearer <token>`.
- Backend verifies every protected request with Firebase Admin SDK.
- Backend never accepts frontend-provided role claims without database confirmation.

Future hardening:

- Firebase custom claims for coarse role hints.
- httpOnly backend session cookies if required.
- Organization/team scope.

## 8. Encryption And Secrets

- Store `DATABASE_URL` only in backend environment.
- Do not expose Supabase keys in frontend.
- Store Firebase Admin SDK credentials only in backend environment.
- Frontend may expose Firebase web config values required by Firebase client SDK.
- Do not commit `.env`.
- Use platform secret stores on Vercel/Render/Railway.
- Use HTTPS in deployed environments.

## 9. Input Validation

Validate:

- latitude/longitude ranges
- event type enum
- event cause enum
- severity enum
- datetime format
- CSV extension and size
- required CSV columns
- report description length and sanitization

## 10. Rate Limiting

Apply to:

- `/api/reports/congestion`: 10/min/IP demo default
- `/api/datasets/upload`: Level 1 admin/control-room only, 3/hour
- `/api/events/simulate`: 60/min/IP demo default

## 11. Audit Logging

MVP logs:

- dataset load
- event simulation
- citizen report submission
- live escalation
- post-event report generation
- officer creation/update/deactivation
- officer field update confirmation
- failed Firebase token validation attempts without logging token values

Future:

- dedicated `system_audit_logs` table

## 12. OWASP Top 10 Mitigations

| Risk | Mitigation |
|---|---|
| Broken access control | Firebase identity plus backend role/assignment checks, backend-only DB access |
| Cryptographic failures | HTTPS, no secrets in frontend |
| Injection | SQLAlchemy parameterization, Pydantic validation |
| Insecure design | confidence scoring for reports, no auto-officialization |
| Security misconfiguration | env-based config, least-exposed endpoints |
| Vulnerable components | dependency scanning in CI |
| Auth failures | Firebase ID token verification and backend role checks |
| Data integrity failures | migration-controlled schema |
| Logging failures | structured logs and audit trail |
| SSRF | no arbitrary backend URL fetches |

## 13. Privacy Controls

Mask or exclude:

```text
veh_no
client_id
created_by_id
last_modified_by_id
assigned_to_police_id
kgid
closed_by_id
resolved_by_id
citizen_accident_id
```

Citizen reports should not collect personal identity in MVP.
