"""Scan History model for tracking user product scans."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlmodel import SQLModel, Field, Relationship


class ScanHistoryBase(SQLModel):
    """Base model for scan history."""
    user_id: str = Field(..., max_length=100, description="User who performed the scan")
    product_id: int = Field(..., foreign_key="products.id", description="Product that was scanned")
    scanned_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False),
        description="When the scan occurred"
    )
    health_score_at_scan: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Health score at time of scan (for history)"
    )
    health_grade_at_scan: Optional[str] = Field(
        default=None,
        max_length=1,
        sa_column=Column(String(1)),
        description="Health grade at time of scan"
    )
    user_feedback: Optional[str] = Field(
        default=None,
        max_length=20,
        sa_column=Column(String(20)),
        description="User feedback: helpful, not_helpful, purchased, avoided"
    )


class ScanHistory(ScanHistoryBase, table=True):
    """Scan history model with relationships."""
    __tablename__ = "scan_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship with Product
    product: Optional["Product"] = Relationship(back_populates="scan_history")
    
    __table_args__ = (
        Index('idx_scan_history_user_id', 'user_id'),
        Index('idx_scan_history_product_id', 'product_id'),
        Index('idx_scan_history_user_scanned', 'user_id', 'scanned_at'),
    )


class ScanHistoryCreate(ScanHistoryBase):
    """Model for creating scan history."""
    pass


class ScanHistoryRead(ScanHistoryBase):
    """Model for reading scan history."""
    id: int


class ScanHistoryUpdate(SQLModel):
    """Model for updating scan history."""
    user_feedback: Optional[str] = Field(None, max_length=20)
