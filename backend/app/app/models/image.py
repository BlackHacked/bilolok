from pathlib import Path

from sqlalchemy import Column, String, ForeignKey
from fastapi_users_db_sqlalchemy import GUID
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.db.base_class import Base
from app.db.mixins import TimeMixin


class Image(Base, TimeMixin):
    """SQLAlchemy images table definition."""
    
    __tablename__ = "image"

    file_id = Column(String, unique=True, nullable=False)
    filename = Column(String)
    filetype = Column(String)
    # Relationships
    user_id = Column(GUID, ForeignKey("user.id"), nullable=False)
    nakamal_id = Column(GUID, ForeignKey("nakamal.id"), nullable=False)
    nakamal = relationship("Nakamal", lazy="joined")

    @staticmethod
    def build_filepath(nakamal_id: str, file_id: str, filename: str):
        IMAGE_PATH_FMT = "nakamals/{subdir}/{n_id}/{f_id}{ext}"
        return Path(IMAGE_PATH_FMT.format(
            subdir=str(nakamal_id)[:2],
            n_id=str(nakamal_id),
            f_id=file_id,
            ext=Path(filename).suffix,
        ))

    @property
    def filepath(self):
        """Relative path to file."""
        return self.build_filepath(
            nakamal_id=self.nakamal_id,
            file_id=self.file_id,
            filename=self.filename,
        )

    @property
    def full_filepath(self):
        """Full path to file."""
        return Path(settings.IMAGES_LOCAL_DIR) / self.filepath
