import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Enum, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

class DraftStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"

class Draft(Base):
    __tablename__ = "drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(String, index=True, nullable=False)
    status = Column(Enum(DraftStatus), default=DraftStatus.DRAFT, nullable=False)
    content = Column(JSON, nullable=True)
    scheduled_time = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(String, index=True, nullable=False)
    s3_key = Column(String, nullable=False)
    url = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

