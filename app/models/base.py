from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, Integer, DateTime, func
from sqlmodel import SQLModel

class Base:
    """Base model class that includes common columns and methods."""
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

# Create the SQLAlchemy base class
Base = declarative_base(cls=Base)

# Also create SQLModel base for compatibility
SQLModelBase = declarative_base()
