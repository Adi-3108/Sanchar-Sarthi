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
