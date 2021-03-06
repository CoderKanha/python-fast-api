from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship
from app.database import Base

class Posts(Base):
    __tablename__ = 'posts'
    id = Column('id', Integer, nullable=False, primary_key=True)
    title = Column('title', String, nullable=False)
    content = Column('content', String, nullable=False)
    is_published = Column('is_published', Boolean, nullable=False, server_default=text('True'))
    is_deleted = Column('is_deleted', Boolean, nullable=False, server_default=text('False'))
    created_at = Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    owner_id = Column('owner_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    owner = relationship('UserModel')