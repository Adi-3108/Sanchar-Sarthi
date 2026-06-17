class _PlaceholderField:
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, _: object) -> bool:
        return True


class UserAccount:
    auth_provider = _PlaceholderField("auth_provider")
    auth_provider_uid = _PlaceholderField("auth_provider_uid")

    def __init__(
        self,
        *,
        id: str = "user-account-id",
        role: str = "admin",
        is_active: bool = True,
        auth_provider: str = "firebase",
        auth_provider_uid: str = "firebase-uid",
    ) -> None:
        self.id = id
        self.role = role
        self.is_active = is_active
        self.auth_provider = auth_provider
        self.auth_provider_uid = auth_provider_uid
