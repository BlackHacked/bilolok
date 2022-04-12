import uuid
from typing import ForwardRef, List, Optional
# from app.schemas.checkin import CheckinSchema

from fastapi_users import models
from pydantic import AnyHttpUrl

from app.schemas.base import BaseSchema

# TODO update schema class names to match other schemas naming convention


class User(models.BaseUser):
    pass


class UserCreate(models.BaseUserCreate):
    pass


class UserUpdate(models.BaseUserUpdate):
    avatar_filename: Optional[str] = None


class UserDB(User, models.BaseUserDB):
    pass
    # avatar: Optional[AnyHttpUrl] = None


# Additional schema for public facing API
class UserSchema(BaseSchema):
    id: uuid.UUID
    avatar: Optional[AnyHttpUrl] = None


CheckinSchema = ForwardRef("CheckinSchema")


class UserSchemaDetails(UserSchema):
    latest_checkin: Optional[CheckinSchema]


from app.schemas.checkin import CheckinSchema
UserSchemaDetails.update_forward_refs()