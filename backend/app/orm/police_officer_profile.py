class _PlaceholderField:
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, _: object) -> bool:
        return True

    def is_(self, _: object) -> bool:
        return True


class PoliceOfficerProfile:
    user_account_id = _PlaceholderField("user_account_id")
    active = _PlaceholderField("active")

    def __init__(
        self,
        *,
        id: str = "officer-profile-id",
        officer_id: str = "BTP-DEMO-001",
        police_station: str | None = None,
        active: bool = True,
    ) -> None:
        self.id = id
        self.officer_id = officer_id
        self.police_station = police_station
        self.active = active
