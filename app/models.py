from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(10))  # "site" or "tg"
    url: Mapped[str] = mapped_column(String(512), unique=True)
    enabled: Mapped[bool] = mapped_column(default=True)


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(255), unique=True)


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    summary: Mapped[Optional[str]]
    source: Mapped[str] = mapped_column(String(255))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw_text: Mapped[Optional[str]]

    __table_args__ = (
        UniqueConstraint("source", "title", name="uq_news_items_source_title"),
        UniqueConstraint("source", "url", name="uq_news_items_source_url"),
        Index("ix_news_items_published_at", "published_at"),
        Index("ix_news_items_source", "source"),
    )

    posts: Mapped[List["Post"]] = relationship(
        "Post", back_populates="news_item", cascade="all, delete-orphan"
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    news_id: Mapped[int] = mapped_column(
        ForeignKey("news_items.id", name="posts_news_id_fkey", ondelete="CASCADE")
    )
    generated_text: Mapped[str]
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="new")
    # status values: new / generated / published / failed

    __table_args__ = (Index("ix_posts_status", "status"),)

    news_item: Mapped["NewsItem"] = relationship("NewsItem", back_populates="posts")
