from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from ..models.user_model import User
from ..repositories.user_repository import UserRepository, get_user_repository
from ..schemas.models import UserResponse


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    @staticmethod
    async def get_user_info(user: User) -> UserResponse:
        return UserResponse.model_validate(user)


def get_user_service(user_repository: Annotated[UserRepository, Depends(get_user_repository)]) -> UserService:
    return UserService(user_repository=user_repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
