"""initial schema: shows, episodes, artworks, publish_runs

Revision ID: 0001
Revises:
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(200), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("section", sa.String(50), nullable=True),
        sa.Column("synopsis", sa.Text, nullable=False, server_default=""),
        sa.Column("categories", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
    )
    op.create_index("ix_shows_slug", "shows", ["slug"])
    op.create_index("ix_shows_section", "shows", ["section"])

    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("episode_id", sa.String(50), nullable=False, unique=True),
        sa.Column("show_id", sa.Integer, sa.ForeignKey("shows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("season_number", sa.Integer, nullable=False),
        sa.Column("episode_number", sa.Integer, nullable=False),
        sa.Column("episode_title", sa.String(300), nullable=False),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("content_group", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.UniqueConstraint("show_id", "season_number", "episode_number", "language",
                             name="uq_episode_position_per_language"),
    )
    op.create_index("ix_episodes_episode_id", "episodes", ["episode_id"])
    op.create_index("ix_episode_content_group_language", "episodes", ["content_group", "language"])
    op.create_index("ix_episode_status", "episodes", ["status"])
    op.create_index("ix_episodes_show_id", "episodes", ["show_id"])

    # NOTE: deliberately NO hard DB constraint on (content_group, language)
    # among published rows. The seed data ships with exactly this collision
    # already committed as fact (ep_0004 vs ep_9001, both 'published'), and
    # a hard constraint would make that state un-seedable -- i.e. it would
    # hide the very problem the exercise wants surfaced. Instead:
    #   - new creates/updates are checked in services/validation.py and
    #     rejected with a 409 before they can introduce a new collision
    #   - existing collisions (however they got there) are detected by a
    #     query in the validation report and block publish
    # This is the intentional trade-off: prevent new damage, always report
    # existing damage, never silently normalize it away.

    op.create_table(
        "artworks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("episode_id", sa.Integer, sa.ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("width", sa.Integer, nullable=False),
        sa.Column("height", sa.Integer, nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.UniqueConstraint("episode_id", "kind", name="uq_artwork_episode_kind"),
    )
    op.create_index("ix_artworks_episode_id", "artworks", ["episode_id"])

    op.create_table(
        "publish_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("triggered_by", sa.String(100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(20), nullable=False, server_default="running"),
        sa.Column("shows_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("episodes_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("catalog_storage_key", sa.String(500), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
    )


def downgrade():
    op.drop_table("publish_runs")
    op.drop_table("artworks")
    op.drop_table("episodes")
    op.drop_table("shows")