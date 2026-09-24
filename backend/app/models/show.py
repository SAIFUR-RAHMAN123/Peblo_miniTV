from sqlalchemy import ARRAY, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    section: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    synopsis: Mapped[str] = mapped_column(Text, default="")
    categories: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    episodes: Mapped[list["Episode"]] = relationship(
        back_populates="show", cascade="all, delete-orphan",
        order_by="Episode.season_number,Episode.episode_number"
    )