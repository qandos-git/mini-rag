from .miniragdb_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Index
import uuid

'''
JSONB best for apps with losts **reading** operations
JSON best for apps with losts **writing** operations

Any uniqu values columns are indexed by default
'''

class Asset(SQLAlchemyBase):
     __tablename__ = "assets"
     
     asset_id = Column(Integer, primary_key=True, autoincrement=True) 
     asset_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

     asset_type = Column(String, nullable=False)
     asset_name = Column(String, nullable=False)
     asset_size = Column(Integer,nullable=False ) 
     asset_config = Column(JSONB, nullable=True)

     created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
     updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

     project = relationship("Project", back_populates="assets")

     asset_project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
     chunks = relationship("DataChunk", back_populates="asset")


     __table_args__ = (
          Index('ix_asset_project_id', asset_project_id),
     )
