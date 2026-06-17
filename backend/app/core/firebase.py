from typing import Any

from app.core.config import Settings

try:
    import firebase_admin
    from firebase_admin import credentials
except ModuleNotFoundError:  # pragma: no cover - exercised before dependency install
    firebase_admin = None
    credentials = None


def initialize_firebase(settings: Settings) -> Any | None:
    if firebase_admin is None or credentials is None:
        return None

    if firebase_admin._apps:
        return firebase_admin.get_app()

    if (
        not settings.firebase_project_id
        or not settings.firebase_client_email
        or not settings.firebase_private_key
    ):
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
