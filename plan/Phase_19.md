# PHASE 19 — Google Translate Multilingual Report Intelligence

## Phase Overview

Add optional Google Cloud Translation support so citizen/field reports can be accepted in any language, translated into English for EventFlow AI reasoning, and preserved in the original language for audit.

This phase extends EventFlow AI beyond the free-only MVP. Google Translate API requires Google Cloud credentials and may require billing after free credits/free quotas. Therefore, this phase must be implemented as an optional provider that is disabled by default unless explicit environment variables are configured.

---

## Why This Phase Exists

- **Problem being solved:** Citizens may report congestion in Kannada, Hindi, English, Tamil, Telugu, Urdu, Marathi, or mixed local language text. Static dictionaries cannot reliably understand arbitrary report descriptions.
- **User need addressed:** Public users should be able to report quickly in the language they are comfortable with.
- **Business requirement satisfied:** This strengthens real-world impact, inclusivity, and live-report quality.
- **Why now:** This phase depends on Phase 11 citizen/field reports and improves Phase 12 live escalation and Phase 06 Event DNA text context.
- **How it contributes:** It turns multilingual public reports into normalized English operational signals while preserving raw citizen text.

---

## Scope Decision

Phase 19 changes the earlier strict "no paid API" constraint.

MVP default:

- Google Translate disabled.
- Static English/Kannada/Hindi labels still work.
- Unknown-language reports are accepted and stored.

Optional enhanced mode:

- Google Translate enabled server-side.
- Any report language can be translated to English for backend reasoning.
- Budget guardrails prevent runaway usage.

Judge-safe wording:

```text
EventFlow AI can accept reports in any language. In the base MVP, structured fields and static English/Kannada/Hindi labels work without paid APIs. With optional Google Cloud Translation enabled, report descriptions are translated to English for Event DNA, report confidence, and live escalation while preserving the original text.
```

---

## Expected Outcome

After completion:

- **New functionality:** Any-language report descriptions can be translated to English.
- **New APIs:** POST /api/translation/normalize; translation fields in POST /api/reports/congestion.
- **New workflows:** Citizen report -> language detection -> translation -> confidence scoring -> event matching -> live escalation.
- **New infrastructure:** backend/app/services/translation_service.py; backend/app/api/routes_translation.py; backend/app/core/translation_budget.py.
- **New data models:** additional translation columns on citizen_reports.

---

## Full Implementation Requirements

Implementation agents must create executable source files for every path listed in this phase.

Required implementation standards:

- Google Translate calls must happen only from the backend.
- Never expose Google Cloud credentials in frontend code.
- Translation must be optional and disabled if credentials/env vars are missing.
- Raw report text must always be stored.
- Translated text must be stored separately.
- If translation fails, report submission must still succeed with `translation_status = "failed"` or `"disabled"`.
- Use translated English only as supporting text context. Structured fields such as report type, severity, and location remain primary.
- Add budget guardrails and logging.

### Exact Repository Paths For This Phase

- backend/app/services/translation_service.py
- backend/app/core/translation_budget.py
- backend/app/api/routes_translation.py
- backend/app/schemas/translation_schema.py
- backend/tests/test_translation_service.py

---

## Implementation Code Snippets

### Environment Variables

```env
GOOGLE_TRANSLATE_ENABLED=false
GOOGLE_TRANSLATE_PROVIDER=google
GOOGLE_TRANSLATE_TARGET_LANGUAGE=en
GOOGLE_TRANSLATE_DAILY_CHAR_LIMIT=50000
GOOGLE_TRANSLATE_MONTHLY_CHAR_LIMIT=500000
GOOGLE_TRANSLATE_FAIL_OPEN=true
GOOGLE_CLOUD_PROJECT_ID=eventflow-ai-demo
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
```

Rules:

- `GOOGLE_APPLICATION_CREDENTIALS_JSON` is backend-only.
- Do not use `NEXT_PUBLIC_*` for Google credentials.
- Keep `GOOGLE_TRANSLATE_ENABLED=false` in default local/demo `.env.example` unless the team intentionally enables it.

### `backend/app/schemas/translation_schema.py`

```python
from pydantic import BaseModel, Field

class TranslationNormalizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    source_language: str | None = Field(default=None, max_length=16)
    target_language: str = Field(default='en', max_length=16)
    purpose: str = Field(default='citizen_report', max_length=40)

class TranslationNormalizeResponse(BaseModel):
    original_text: str
    source_language: str
    target_language: str
    translated_text: str | None
    provider: str
    status: str
    character_count: int
```

### `backend/app/core/translation_budget.py`

```python
from dataclasses import dataclass
from datetime import date

@dataclass
class TranslationUsageState:
    day: date
    month: str
    daily_characters: int = 0
    monthly_characters: int = 0

class TranslationBudgetGuard:
    def __init__(self, daily_limit: int, monthly_limit: int):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        today = date.today()
        self.state = TranslationUsageState(day=today, month=today.strftime('%Y-%m'))

    def _rollover_if_needed(self) -> None:
        today = date.today()
        current_month = today.strftime('%Y-%m')
        if self.state.day != today:
            self.state.day = today
            self.state.daily_characters = 0
        if self.state.month != current_month:
            self.state.month = current_month
            self.state.monthly_characters = 0

    def can_spend(self, character_count: int) -> bool:
        self._rollover_if_needed()
        return (
            self.state.daily_characters + character_count <= self.daily_limit
            and self.state.monthly_characters + character_count <= self.monthly_limit
        )

    def record(self, character_count: int) -> None:
        self._rollover_if_needed()
        self.state.daily_characters += character_count
        self.state.monthly_characters += character_count
```

### `backend/app/services/translation_service.py`

```python
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
        return translate.Client(credentials=credentials, project=self.settings.google_cloud_project_id)

    def normalize(self, text: str, source_language: str | None = None, target_language: str = 'en') -> TranslationResult:
        character_count = len(text)

        if not self.settings.google_translate_enabled or self.client is None:
            return TranslationResult(text, source_language or 'unknown', target_language, None, 'disabled', 'disabled', character_count)

        if not self.budget_guard.can_spend(character_count):
            return TranslationResult(text, source_language or 'unknown', target_language, None, 'google', 'budget_blocked', character_count)

        try:
            detected = source_language
            if not detected:
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
```

### `backend/app/api/routes_translation.py`

```python
from fastapi import APIRouter, Depends
from app.core.config import get_settings
from app.core.translation_budget import TranslationBudgetGuard
from app.schemas.translation_schema import TranslationNormalizeRequest, TranslationNormalizeResponse
from app.services.translation_service import TranslationService

router = APIRouter(prefix='/api/translation', tags=['translation'])

def get_translation_service() -> TranslationService:
    settings = get_settings()
    budget = TranslationBudgetGuard(
        daily_limit=settings.google_translate_daily_char_limit,
        monthly_limit=settings.google_translate_monthly_char_limit,
    )
    return TranslationService(settings=settings, budget_guard=budget)

@router.post('/normalize', response_model=TranslationNormalizeResponse)
def normalize_translation(
    payload: TranslationNormalizeRequest,
    service: TranslationService = Depends(get_translation_service),
) -> TranslationNormalizeResponse:
    result = service.normalize(
        text=payload.text,
        source_language=payload.source_language,
        target_language=payload.target_language,
    )
    return TranslationNormalizeResponse(**result.__dict__)
```

### Citizen Report Integration

```python
def normalize_report_description(description: str, language: str | None, translation_service: TranslationService) -> dict[str, object]:
    result = translation_service.normalize(
        text=description,
        source_language=language,
        target_language='en',
    )
    return {
        'description': description,
        'source_language': result.source_language,
        'translated_description': result.translated_text,
        'translation_provider': result.provider,
        'translation_status': result.status,
        'translation_character_count': result.character_count,
    }
```

Report confidence and Event DNA should use:

```text
translated_description if translation_status in translated/source_already_target
else description only for storage/audit, not for semantic scoring
```

---

## Database Requirements

Add these columns to `citizen_reports`:

| Column | Type | Notes |
|---|---|---|
| source_language | text | detected or user-selected language |
| translated_description | text | English translation for backend reasoning |
| translation_provider | text | disabled, google |
| translation_status | text | disabled, translated, source_already_target, budget_blocked, failed |
| translation_character_count | integer | cost/budget accounting |

Optional future table:

```sql
CREATE TABLE IF NOT EXISTS translation_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL,
    purpose TEXT NOT NULL,
    source_language TEXT,
    target_language TEXT NOT NULL DEFAULT 'en',
    character_count INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## API Requirements

- **POST /api/translation/normalize:** protected or internal endpoint for testing translation.
- **POST /api/reports/congestion:** must call translation service when enabled.
- **Failure behavior:** report submission succeeds even if translation fails when `GOOGLE_TRANSLATE_FAIL_OPEN=true`.

---

## Frontend Requirements

- Citizen report form should allow language selection:
  - auto
  - English
  - Kannada
  - Hindi
  - other
- UI labels can remain static English/Kannada/Hindi.
- Description text can be typed in any language.
- Frontend must not call Google Translate directly.
- Frontend must not expose Google Cloud credentials.

---

## Security Requirements

- Store Google Cloud credentials only in backend secrets.
- Do not translate sensitive identifiers such as vehicle numbers if detected; mask first where possible.
- Limit description length before translation.
- Rate-limit translation endpoints.
- Log character counts, not full translated text, in operational logs.
- Translation output is supporting context, not official evidence by itself.

---

## Testing Requirements

Unit tests:

- disabled provider returns `translation_status = disabled`.
- same-language English text returns `source_already_target`.
- budget exceeded returns `budget_blocked`.
- Google exception returns `failed` when fail-open is true.
- report submission succeeds if translation fails.

Integration tests:

- Kannada report -> English `translated_description`.
- Hindi report -> English `translated_description`.
- Unknown language report -> source detected and translated when provider is enabled.
- Translation fields are persisted in `citizen_reports`.

---

## Validation Commands

```bash
pytest backend/tests/test_translation_service.py backend/tests/test_citizen_reports.py
```

---

## Completion Criteria

Phase is complete only if:

- Google Translate integration is backend-only.
- Translation is disabled safely without credentials.
- Report submission never depends entirely on translation.
- Budget guardrails work.
- Translation fields are persisted.
- Existing English/Kannada/Hindi static UI still works.
- No Google credentials appear in frontend or `NEXT_PUBLIC_*`.
