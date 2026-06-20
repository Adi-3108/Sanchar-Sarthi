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
