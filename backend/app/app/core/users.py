from pathlib import Path
from typing import List, Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
import pydenticon
from sqlalchemy import select

from app.core.config import settings
from app.core.mail import mail, MessageSchema
from app.db.session import async_session
from app.models.fastapi_users_db_sqlalchemy_asyncpg import SQLAlchemyUserDatabase
from app.models.user import User as UserTable
from app.schemas.user import User, UserCreate, UserUpdate, UserDB


class UserManager(BaseUserManager[UserCreate, UserDB]):
    user_db_model = UserDB
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def get_multi(self) -> List[UserDB]:
        users = await self.user_db.get_multi()
        return users

    async def on_after_register(self, user: UserDB, request: Optional[Request] = None) -> None:
        print(f"User {user.id} has registered.")
        message = MessageSchema(
            subject="Welcome to Bilolok!",
            recipients=[user.email],
            body="Thanks for joining! You can also join our Facebook group to give feedback and suggest improvements for Bilolok."
        )
        await mail.send_message(message)
        # Render user's default avatar image
        relativeAvatarPath = UserTable.build_avatar_filepath(user.id)
        fullAvatarPath = Path(settings.IMAGES_LOCAL_DIR) / relativeAvatarPath
        fullAvatarPath.parent.mkdir(parents=True, exist_ok=True)
        icon = pydenticon.Generator(5, 5)
        identicon = icon.generate(str(user.id), 200, 200)
        with fullAvatarPath.open("wb") as f:
            f.write(identicon)

    async def on_after_forgot_password(self, user: UserDB, token: str, request: Optional[Request] = None) -> None:
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(self, user: UserDB, token: str, request: Optional[Request] = None) -> None:
        print(f"Verification requested for user {user.id}. Verification token: {token}")


jwt_authentication = JWTAuthentication(
    secret=settings.SECRET_KEY,
    lifetime_seconds=3600,
    tokenUrl="/api/v1/auth/jwt/login",
    token_audience=[f"{settings.PROJECT_SLUG}:auth"]
)


class MySQLAlchemyUserDatabase(SQLAlchemyUserDatabase):
    async def get_multi(self) -> List[UserDB]:
        async with self.session.begin() as session:
            query = select(self.users)
            result = await session.execute(query)
            users = result.all()

        return [await self._make_user(user) for user in users] if users else None


async def get_user_db():
    yield MySQLAlchemyUserDatabase(UserDB, async_session, UserTable.__table__)


async def get_user_manager(user_db: MySQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


fastapi_users = FastAPIUsers(
    get_user_manager,
    [jwt_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)