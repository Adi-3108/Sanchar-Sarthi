# EventFlow AI Firebase Auth Implementation

## 1. Decision

EventFlow AI uses Firebase Auth for MVP identity and PostgreSQL for authorization.

Firebase answers: "Who is this user?"

EventFlow AI backend answers: "What is this user allowed to do?"

This separation is mandatory because Firebase login alone must not grant command-center or officer permissions.

## 2. Access Model

| Level | User | Login | Backend authorization |
|---|---|---|---|
| Level 1 | Admin / Control Room | Firebase email/password | `user_accounts.role IN ('admin', 'control_room')` and `is_active = true` |
| Level 2 | Registered Police Officer | Firebase email/password | `user_accounts.role = 'police_officer'`, active officer profile, and assignment check |
| Level 3 | Public / Citizen | No login | rate-limited public-safe endpoints only |

## 3. Required Environment Variables

Backend-only:

```env
FIREBASE_PROJECT_ID=eventflow-ai-demo
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@eventflow-ai-demo.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

Frontend-safe:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=public_web_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=eventflow-ai-demo.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=eventflow-ai-demo
```

Never expose `FIREBASE_CLIENT_EMAIL` or `FIREBASE_PRIVATE_KEY` in frontend code.

## 4. Frontend Firebase Client

`frontend/lib/firebase.ts`

```ts
import { initializeApp, getApps } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY!,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN!,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID!,
};

const firebaseApp = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);

export const firebaseAuth = getAuth(firebaseApp);
```

`frontend/lib/auth.ts`

```ts
import {
  browserLocalPersistence,
  onAuthStateChanged,
  setPersistence,
  signInWithEmailAndPassword,
  signOut,
  type User,
} from 'firebase/auth';
import { firebaseAuth } from './firebase';

export type FirebaseSession = {
  uid: string;
  email: string | null;
  idToken: string;
};

export async function loginWithFirebase(email: string, password: string): Promise<FirebaseSession> {
  await setPersistence(firebaseAuth, browserLocalPersistence);
  const credential = await signInWithEmailAndPassword(firebaseAuth, email, password);
  const idToken = await credential.user.getIdToken();
  return {
    uid: credential.user.uid,
    email: credential.user.email,
    idToken,
  };
}

export async function getCurrentFirebaseToken(forceRefresh = false): Promise<string | undefined> {
  const user = firebaseAuth.currentUser;
  if (!user) return undefined;
  return user.getIdToken(forceRefresh);
}

export function listenToFirebaseUser(callback: (user: User | null) => void): () => void {
  return onAuthStateChanged(firebaseAuth, callback);
}

export async function logoutFirebase(): Promise<void> {
  await signOut(firebaseAuth);
}
```

`frontend/lib/authHeaders.ts`

```ts
import { getCurrentFirebaseToken } from './auth';

export async function authHeaders(): Promise<HeadersInit> {
  const token = await getCurrentFirebaseToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}
```

## 5. Backend Firebase Initialization

`backend/app/core/firebase.py`

```python
import firebase_admin
from firebase_admin import credentials
from app.core.config import Settings

def initialize_firebase(settings: Settings) -> firebase_admin.App | None:
    if firebase_admin._apps:
        return firebase_admin.get_app()

    if not settings.firebase_project_id or not settings.firebase_client_email or not settings.firebase_private_key:
        return None

    private_key = settings.firebase_private_key.replace("\\n", "\n")
    cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": settings.firebase_project_id,
            "client_email": settings.firebase_client_email,
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )
    return firebase_admin.initialize_app(cred)
```

Call this once during FastAPI startup.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import get_settings
from app.core.firebase import initialize_firebase

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_firebase(get_settings())
    yield

app = FastAPI(title="EventFlow AI", lifespan=lifespan)
```

## 6. Backend Auth Context And Guards

`backend/app/core/security.py`

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
    firebase_uid = token_payload["uid"]
    account = (
        db.query(UserAccount)
        .filter(UserAccount.auth_provider == "firebase")
        .filter(UserAccount.auth_provider_uid == firebase_uid)
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
        firebase_uid=firebase_uid,
        email=token_payload.get("email"),
        role=account.role,
        user_account_id=str(account.id),
        officer_profile_id=str(officer_profile.id) if officer_profile else None,
        officer_id=officer_profile.officer_id if officer_profile else None,
        police_station=officer_profile.police_station if officer_profile else None,
        assigned_corridors=officer_profile.assigned_corridors_json if officer_profile else None,
        assigned_zones=officer_profile.assigned_zones_json if officer_profile else None,
    )

def get_auth_context(
    token_payload: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db),
) -> AuthContext:
    return load_auth_context(db, token_payload)

def require_role(*allowed_roles: str):
    def dependency(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if auth.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "FORBIDDEN_ROLE"})
        return auth
    return dependency
```

Officer assignment checks should be added in route/service dependencies that know the `event_id`, corridor, station, or zone being accessed. The `AuthContext` carries the officer's station, assigned corridors, and assigned zones for fast checks, while `officer_event_assignments` remains the source of truth for event-specific assignments.

## 7. Protected Endpoint Pattern

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import AuthContext, require_role
from app.db.session import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/officers")
def create_officer(
    payload: CreateOfficerRequest,
    auth: AuthContext = Depends(require_role("admin", "control_room")),
    db: Session = Depends(get_db),
) -> CreateOfficerResponse:
    return officer_management_service.create_officer(db=db, payload=payload, created_by=auth)
```

## 8. Officer Creation Workflow

MVP workflow:

1. Level 1 admin creates/invites officer in Firebase Console or through Firebase Admin SDK.
2. Admin copies the Firebase UID into the EventFlow admin form.
3. Backend creates:
   - `user_accounts.auth_provider = 'firebase'`
   - `user_accounts.auth_provider_uid = <firebase_uid>`
   - `user_accounts.role = 'police_officer'`
   - `police_officer_profiles.user_account_id = user_accounts.id`
   - assignment rows in `officer_event_assignments`
4. Officer logs in with Firebase email/password.
5. Backend maps token UID to the officer profile and assignment scope.

Optional implementation upgrade:

```python
from firebase_admin import auth as firebase_auth

def create_firebase_user_for_officer(email: str, temporary_password: str) -> str:
    user = firebase_auth.create_user(email=email, password=temporary_password, email_verified=False)
    return user.uid
```

For hackathon MVP, manual Firebase Console user creation is acceptable because it is free and avoids SMS/OTP cost.

## 9. Public Access

Public citizen endpoints must not require Firebase login. They must use:

- coordinate validation
- text length limits
- rate limiting by IP/session
- confidence scoring
- officer/admin confirmation before becoming official

## 10. Required Tests

- Missing `Authorization` header returns `MISSING_FIREBASE_TOKEN`.
- Invalid token returns `INVALID_FIREBASE_TOKEN`.
- Revoked token returns `REVOKED_FIREBASE_TOKEN`.
- Valid Firebase token with no `user_accounts` row returns `INACTIVE_ACCOUNT`.
- Inactive account returns `INACTIVE_ACCOUNT`.
- Officer without profile returns `OFFICER_PROFILE_REQUIRED`.
- Wrong role returns `FORBIDDEN_ROLE`.
- Public report endpoint works without Firebase token and still rate-limits.
- Frontend never bundles `FIREBASE_PRIVATE_KEY` or `FIREBASE_CLIENT_EMAIL`.
