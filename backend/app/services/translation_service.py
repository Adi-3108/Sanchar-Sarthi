import json
from dataclasses import dataclass
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from app.core.config import Settings
from app.core.translation_budget import TranslationBudgetGuard

@dataclass(frozen=True)
class TranslationResult:
    original_text: str
    source_language: str
    target_language: str
    translated_text: str | None
    provider: str
    status: str
    character_count: int

class TranslationService:
    def __init__(self, settings: Settings, budget_guard: TranslationBudgetGuard):
        self.settings = settings
        self.budget_guard = budget_guard
        self.client = self._build_client()

    def _build_client(self):
        if not self.settings.google_translate_enabled:
            return None
        if not self.settings.google_application_credentials_json:
            return None
        credentials_info = json.loads(self.settings.google_application_credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        return translate.Client(credentials=credentials)

    def normalize(self, text: str, source_language: str | None = None, target_language: str = 'en') -> TranslationResult:
        character_count = len(text)

        if not self.settings.google_translate_enabled or self.client is None:
            return TranslationResult(text, source_language or 'unknown', target_language, None, 'disabled', 'disabled', character_count)

        if not self.budget_guard.can_spend(character_count):
            return TranslationResult(text, source_language or 'unknown', target_language, None, 'google', 'budget_blocked', character_count)

        try:
            detected = source_language
            if not detected or detected in ('auto', 'other'):
                detection = self.client.detect_language(text)
                detected = detection.get('language') or 'unknown'
            if detected == target_language:
                translated_text = text
                status = 'source_already_target'
            else:
                translated = self.client.translate(text, source_language=detected if detected != 'unknown' else None, target_language=target_language)
                translated_text = translated.get('translatedText')
                status = 'translated'
            self.budget_guard.record(character_count)
            return TranslationResult(text, detected, target_language, translated_text, 'google', status, character_count)
        except Exception:
            if self.settings.google_translate_fail_open:
                return TranslationResult(text, source_language or 'unknown', target_language, None, 'google', 'failed', character_count)
            raise
