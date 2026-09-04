from abc import ABC, abstractmethod


class AuthProvider(ABC):
    @abstractmethod
    def get_login_url(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify_token(self, code: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_user_info(self, credentials) -> dict:
        raise NotImplementedError

    @abstractmethod
    def validate_state(self, state: str) -> bool:
        raise NotImplementedError