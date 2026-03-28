import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from noetikon.models.base import Base


class LLMUsage(Base):
    __tablename__ = "llm_usage"
    __table_args__ = (Index("ix_group_created", "group_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
