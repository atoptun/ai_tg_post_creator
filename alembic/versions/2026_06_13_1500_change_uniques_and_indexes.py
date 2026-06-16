"""Change unique constraints to be source-scoped and add indexes

Revision ID: b1c2d3e4f567
Revises: a5c208b630cb
Create Date: 2026-06-13 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f567"
down_revision: Union[str, Sequence[str], None] = "a5c208b630cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop old unique constraints on news_items
    op.drop_constraint(op.f("uq_news_items_title"), "news_items", type_="unique")
    op.drop_constraint(op.f("uq_news_items_url"), "news_items", type_="unique")

    # Create new source-scoped unique constraints
    op.create_unique_constraint(
        "uq_news_items_source_title", "news_items", ["source", "title"]
    )
    op.create_unique_constraint(
        "uq_news_items_source_url", "news_items", ["source", "url"]
    )

    # Add useful indexes
    op.create_index("ix_news_items_published_at", "news_items", ["published_at"])
    op.create_index("ix_news_items_source", "news_items", ["source"])
    op.create_index("ix_posts_status", "posts", ["status"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_posts_status", table_name="posts")
    op.drop_index("ix_news_items_source", table_name="news_items")
    op.drop_index("ix_news_items_published_at", table_name="news_items")

    op.drop_constraint("uq_news_items_source_url", "news_items", type_="unique")
    op.drop_constraint("uq_news_items_source_title", "news_items", type_="unique")

    op.create_unique_constraint(op.f("uq_news_items_url"), "news_items", ["url"])
    op.create_unique_constraint(op.f("uq_news_items_title"), "news_items", ["title"])
