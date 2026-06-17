from app.core.config import Settings
from app.core.firebase import initialize_firebase


def test_initialize_firebase_returns_none_without_credentials():
    settings = Settings(
        FIREBASE_PROJECT_ID=None,
        FIREBASE_CLIENT_EMAIL=None,
        FIREBASE_PRIVATE_KEY=None,
    )

    assert initialize_firebase(settings) is None
