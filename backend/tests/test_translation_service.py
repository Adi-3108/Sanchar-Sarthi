from datetime import date
from unittest.mock import MagicMock
import pytest
from app.core.translation_budget import TranslationBudgetGuard
from app.services.translation_service import TranslationService
from app.core.config import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        google_translate_enabled=True,
        google_application_credentials_json='{"type": "service_account"}',
        google_cloud_project_id="test-project",
        google_translate_daily_char_limit=1000,
        google_translate_monthly_char_limit=5000,
        google_translate_fail_open=True,
    )

@pytest.fixture
def budget_guard():
    return TranslationBudgetGuard(daily_limit=1000, monthly_limit=5000)

from unittest.mock import MagicMock, patch

@pytest.fixture
def translation_service(mock_settings, budget_guard):
    with patch('app.services.translation_service.service_account.Credentials.from_service_account_info') as mock_creds:
        with patch('app.services.translation_service.translate.Client') as mock_client:
            service = TranslationService(settings=mock_settings, budget_guard=budget_guard)
            service.client = MagicMock()
            return service

def test_disabled_provider_returns_disabled_status(mock_settings, budget_guard):
    mock_settings.google_translate_enabled = False
    service = TranslationService(settings=mock_settings, budget_guard=budget_guard)
    result = service.normalize("Hello world")
    
    assert result.status == "disabled"
    assert result.provider == "disabled"
    assert result.translated_text is None

def test_source_already_target_returns_correct_status(translation_service):
    translation_service.client.detect_language.return_value = {"language": "en"}
    result = translation_service.normalize("Hello world", target_language="en")
    
    assert result.status == "source_already_target"
    assert result.translated_text == "Hello world"
    assert result.source_language == "en"

def test_budget_exceeded_returns_blocked(translation_service):
    translation_service.budget_guard.record(999) # Use up budget
    
    result = translation_service.normalize("Test string") # 11 chars > 1 char remaining
    
    assert result.status == "budget_blocked"
    assert result.translated_text is None
    assert result.provider == "google"

def test_translation_success(translation_service):
    translation_service.client.detect_language.return_value = {"language": "kn"}
    translation_service.client.translate.return_value = {"translatedText": "Traffic jam"}
    
    result = translation_service.normalize("ಟ್ರಾಫಿಕ್ ಜಾಮ್")
    
    assert result.status == "translated"
    assert result.translated_text == "Traffic jam"
    assert result.source_language == "kn"
    assert translation_service.budget_guard.state.daily_characters == len("ಟ್ರಾಫಿಕ್ ಜಾಮ್")

def test_google_exception_returns_failed_when_fail_open_true(translation_service):
    translation_service.client.detect_language.side_effect = Exception("API Error")
    
    result = translation_service.normalize("Error case")
    
    assert result.status == "failed"
    assert result.translated_text is None
