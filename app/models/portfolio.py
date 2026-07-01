from sqlalchemy import Column, Float, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.db import Base


class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(30), nullable=False)
    shares = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)

    user = relationship("User", back_populates="portfolio")

    __table_args__ = (
        UniqueConstraint("user_id", "symbol"),
    )
