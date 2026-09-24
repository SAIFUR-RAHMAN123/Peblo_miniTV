"""drop hard uniqueness on episode position; enforce at app layer instead

The seed data contains a genuine duplicate (ep_0004 vs ep_9001: same show,
season 1, episode 2, language 'hi' -- these are also the same
content_group+language collision reported by the validation report). A hard
DB constraint on this tuple makes that state un-loadable, which hides the
exact problem this exercise wants surfaced. New creates/updates are checked
in the API layer instead; existing collisions are reported, not silently
prevented from ever existing.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-05
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uq_episode_position_per_language", "episodes", type_="unique")


def downgrade():
    op.create_unique_constraint(
        "uq_episode_position_per_language", "episodes",
        ["show_id", "season_number", "episode_number", "language"],
    )