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
