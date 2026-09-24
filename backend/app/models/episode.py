from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Episode(Base):
    __tablename__ = "episodes"
    __table_args__ = (
        Index("ix_episode_content_group_language", "content_group", "language"),
        Index("ix_episode_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    episode_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)

    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_title: Mapped[str] = mapped_column(String(300), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    content_group: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    # draft | published. Intentionally NO DB-level unique constraint on
    # (content_group, language) -- the seed data ships with a genuine
    # collision between two published rows (ep_0004 / ep_9001), and a hard
    # constraint would make that un-seedable, hiding the exact problem the
    # exercise wants surfaced. New creates/updates are validated at the
    # service layer; existing collisions are detected by the validation
    # report and block publish.
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    show: Mapped["Show"] = relationship(back_populates="episodes")
    artworks: Mapped[list["Artwork"]] = relationship(back_populates="episode", cascade="all, delete-orphan")