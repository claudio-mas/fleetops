from typing import Any

from fastapi import Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.password import PasswordHelper
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.models.user import User

_password_hash = PasswordHash((Argon2Hasher(),))
_password_helper = PasswordHelper(_password_hash)


class UserManager(UUIDIDMixin, BaseUserManager[User, Any]):
    reset_password_token_secret = ""  # sobrescrito em get_user_manager
    verification_token_secret = ""

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        pass

    async def on_after_login(
        self,
        user: User,
        request: Request | None = None,
        response: Any = None,
    ) -> None:
        pass


async def get_user_db(
    session: Any,
) -> Any:
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: Any) -> Any:
    from app.core.config import settings

    manager = UserManager(user_db, _password_helper)
    manager.reset_password_token_secret = settings.secret_key
    manager.verification_token_secret = settings.secret_key
    yield manager
